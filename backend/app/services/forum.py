"""포럼 글 (docs 07 포럼, F-17·D-42·D-91)

- 글은 수정 불가 (D-05) / 삭제하면 댓글까지 조용히 사라짐 (D-91)
- 목록은 고정글이 맨 위, 그다음 New(최신) 또는 Hot(점수)
- Hot 점수는 문장 정렬과 같은 공식 (docs 04, 포럼용 설정값)
"""

from datetime import UTC, datetime

from sqlalchemy import Row, func, select, update
from sqlalchemy.orm import Session, aliased

from app.config import settings
from app.errors import api_error
from app.models import ForumComment, ForumPost, ForumPostVote, Sentence, User
from app.schemas.forum import (
    PostCreate,
    PostListOut,
    PostOut,
    PostSort,
    PostSummary,
    QuotedSentence,
)
from app.services import limits, managers
from app.services.ranking import rank_score
from app.services.stories import find_visible_story
from app.timeutil import kst_now

# 글마다 붙이는 개수 (저장하지 않고 조회할 때 계산)
_up_count = (
    select(func.count())
    .where(ForumPostVote.post_id == ForumPost.id, ForumPostVote.value == 1)
    .scalar_subquery()
)
_down_count = (
    select(func.count())
    .where(ForumPostVote.post_id == ForumPost.id, ForumPostVote.value == -1)
    .scalar_subquery()
)
_comment_count = (
    select(func.count())
    .where(ForumComment.post_id == ForumPost.id, ForumComment.status != "removed")
    .scalar_subquery()
)
# 인용한 문장 (없을 수도 있어서 바깥 조인)
_quote = aliased(Sentence)


def _my_vote(user_id: int | None):
    """그 글에 내가 누른 표 (없으면 NULL) / 로그인 안 했으면 아무에게도 안 맞는 번호로 조회"""
    return (
        select(ForumPostVote.value)
        .where(
            ForumPostVote.post_id == ForumPost.id,
            ForumPostVote.user_id == (user_id if user_id is not None else -1),
        )
        .scalar_subquery()
    )


def list_posts(
    db: Session, story_id: int, sort: PostSort, page: int, size: int, user_id: int | None = None
) -> PostListOut:
    """스토리의 글 목록. 고정글이 먼저, 그다음 정렬 기준대로

    스토리 하나의 글은 많아야 수십 개라 전부 가져와 Python에서 순서를 정하고 자름
    (Hot 점수를 SQL로 계산하지 않아도 되고, 문장 목록과 같은 방식)
    """
    find_visible_story(db, story_id)

    items = [_to_summary(row) for row in db.execute(_select_posts(user_id, story_id))]
    ordered = _order(items, sort)
    start = (page - 1) * size
    return PostListOut(
        items=ordered[start : start + size],
        page=page,
        size=size,
        total=len(items),
        can_pin=managers.can_pin(db, story_id, user_id),
    )


def get_post(db: Session, post_id: int, user_id: int | None = None) -> PostOut:
    """글 하나. 삭제됐으면 "삭제된 글입니다" (D-91)"""
    row = db.execute(_select_posts(user_id).where(ForumPost.id == post_id)).first()
    if row is None:
        raise post_gone(db, post_id)
    post = row[0]
    # 스토리째 숨겨졌으면 그 안의 글도 보이지 않음
    find_visible_story(db, post.story_id)
    return PostOut(
        **_to_summary(row).model_dump(),
        body=post.body,
        can_pin=managers.can_pin(db, post.story_id, user_id),
    )


def create_post(db: Session, user: User, story_id: int, data: PostCreate) -> PostOut:
    """글 쓰기 (수정은 없음, D-05)"""
    find_visible_story(db, story_id)
    limits.check_new_post(db, user)
    _check_quote(db, story_id, data.quoted_sentence_id)

    post = ForumPost(
        story_id=story_id,
        author_id=user.id,
        title=data.title,
        body=data.body,
        quoted_sentence_id=data.quoted_sentence_id,
    )
    db.add(post)
    db.commit()
    return get_post(db, post.id, user_id=user.id)


def delete_post(db: Session, user: User, post_id: int) -> None:
    """내 글 삭제. 댓글이 있든 없든 글과 댓글이 함께 사라짐 (D-91)"""
    post = db.get(ForumPost, post_id)
    if post is None or post.status == "removed":
        raise post_gone(db, post_id)
    if post.author_id != user.id:
        raise api_error(403, "NOT_MY_POST", "내가 쓴 글만 지울 수 있어요")

    post.status = "removed"
    db.execute(update(ForumComment).where(ForumComment.post_id == post.id).values(status="removed"))
    db.commit()


def _select_posts(user_id: int | None, story_id: int | None = None):
    stmt = (
        select(
            ForumPost,
            User.nickname,
            _up_count,
            _down_count,
            _my_vote(user_id),
            _comment_count,
            _quote.id,
            _quote.content,
        )
        .join(User, User.id == ForumPost.author_id)
        # 인용 문장이 지워졌으면(removed) 인용을 보여주지 않음
        .outerjoin(
            _quote,
            (_quote.id == ForumPost.quoted_sentence_id) & (_quote.status == "active"),
        )
        .where(ForumPost.status != "removed")
    )
    return stmt.where(ForumPost.story_id == story_id) if story_id is not None else stmt


def _order(items: list[PostSummary], sort: PostSort) -> list[PostSummary]:
    """고정글(1·2번 자리)이 맨 위, 나머지는 new = 최신순 / hot = 점수순"""
    pinned = sorted((p for p in items if p.pin_slot), key=lambda p: p.pin_slot or 0)
    rest = [p for p in items if not p.pin_slot]
    if sort == "new":
        rest.sort(key=lambda p: (p.created_at, p.id), reverse=True)
    else:
        now = datetime.now(UTC)
        kst_date = kst_now().date().isoformat()
        rest.sort(key=lambda p: (_hot_score(p, now, kst_date), p.id), reverse=True)
    return pinned + rest


def _hot_score(post: PostSummary, now: datetime, kst_date: str) -> float:
    return rank_score(
        up=post.up_count,
        down=post.down_count,
        age_hours=max((now - post.created_at).total_seconds() / 3600, 0),
        user_id=None,
        item_id=post.id,
        kst_date=kst_date,
        b=settings.forum_rank_b,
        h=settings.forum_rank_h,
        j0=settings.forum_rank_j0,
    )


def _check_quote(db: Session, story_id: int, sentence_id: int | None) -> None:
    """인용은 그 스토리 안의 보이는 문장 1개만 (D-42)"""
    if sentence_id is None:
        return
    found = db.scalar(
        select(Sentence.id).where(
            Sentence.id == sentence_id,
            Sentence.story_id == story_id,
            Sentence.status == "active",
        )
    )
    if found is None:
        raise api_error(404, "QUOTE_NOT_FOUND", "인용할 문장을 찾을 수 없어요")


def _to_summary(row: Row) -> PostSummary:
    post, nickname, up, down, mine, comments, quote_id, quote_content = row
    return PostSummary(
        id=post.id,
        story_id=post.story_id,
        title=post.title,
        author_nickname=nickname,
        created_at=post.created_at,
        up_count=up,
        down_count=down,
        my_vote=mine,
        comment_count=comments,
        pin_slot=post.pin_slot,
        quoted_sentence=(
            QuotedSentence(id=quote_id, content=quote_content) if quote_id is not None else None
        ),
    )


def post_gone(db: Session, post_id: int):
    """지워진 글과 아예 없는 글을 구분해서 알려 줌 (D-91)"""
    if db.scalar(select(ForumPost.id).where(ForumPost.id == post_id)) is not None:
        return api_error(404, "POST_NOT_FOUND", "삭제된 글입니다")
    return api_error(404, "POST_NOT_FOUND", "없는 글이에요")


# 고정은 스토리당 2자리 (D-42·D-91)
PIN_SLOTS = (1, 2)


def pin_post(db: Session, user: User, post_id: int) -> PostOut:
    """글 고정 (창시자·관리자만). 빈 자리가 없으면 거절"""
    post = _pinnable(db, user, post_id)
    if post.pin_slot is None:
        taken = set(
            db.scalars(
                select(ForumPost.pin_slot).where(
                    ForumPost.story_id == post.story_id,
                    ForumPost.pin_slot.is_not(None),
                    ForumPost.status != "removed",
                )
            ).all()
        )
        free = next((slot for slot in PIN_SLOTS if slot not in taken), None)
        if free is None:
            raise api_error(409, "PIN_LIMIT", "고정은 2개까지예요. 먼저 하나를 해제해 주세요")
        post.pin_slot = free
        db.commit()
    return get_post(db, post_id, user_id=user.id)


def unpin_post(db: Session, user: User, post_id: int) -> PostOut:
    """고정 해제 (고정되어 있지 않아도 그냥 성공)"""
    post = _pinnable(db, user, post_id)
    if post.pin_slot is not None:
        post.pin_slot = None
        db.commit()
    return get_post(db, post_id, user_id=user.id)


def _pinnable(db: Session, user: User, post_id: int) -> ForumPost:
    """고정할 수 있는 글인지 (없음·삭제 404 / 권한 없음 403)"""
    post = db.get(ForumPost, post_id)
    if post is None or post.status == "removed":
        raise post_gone(db, post_id)
    find_visible_story(db, post.story_id)
    managers.require_pin_permission(db, post.story_id, user.id)
    return post
