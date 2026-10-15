"""포럼 글 투표 (F-17·D-42)

문장 투표(F-07)와 같은 방식: 1인 1표 · 다시 누르면 취소 · 반대쪽은 바로 전환 · 자기 글 불가 (D-52)
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models import ForumPost, ForumPostVote, User
from app.schemas.forum import PostOut
from app.services.forum import get_post, post_gone
from app.services.stories import find_visible_story


def set_vote(db: Session, user: User, post_id: int, value: int) -> PostOut:
    """추천(1)·비추천(-1) 누르기"""
    post = _votable(db, user, post_id)

    # 거의 동시에 두 번 눌려도 중복으로 터지지 않게 DB가 한 번에 처리
    db.execute(
        insert(ForumPostVote)
        .values(user_id=user.id, post_id=post.id, value=value)
        .on_conflict_do_update(
            index_elements=[ForumPostVote.user_id, ForumPostVote.post_id],
            set_={"value": value},
        )
    )
    db.commit()
    return get_post(db, post_id, user_id=user.id)


def clear_vote(db: Session, user: User, post_id: int) -> PostOut:
    """내 표 취소 (안 눌렀어도 그냥 성공)"""
    _votable(db, user, post_id)

    vote = db.get(ForumPostVote, {"user_id": user.id, "post_id": post_id})
    if vote is not None:
        db.delete(vote)
        db.commit()
    return get_post(db, post_id, user_id=user.id)


def _votable(db: Session, user: User, post_id: int) -> ForumPost:
    """투표할 수 있는 글인지 (없음·삭제 404 / 접힘 409 / 자기 글 403)"""
    post = db.get(ForumPost, post_id)
    if post is None or post.status == "removed":
        raise post_gone(db, post_id)
    # 스토리째 숨겨졌으면 그 안의 글도 없는 것으로 봄
    find_visible_story(db, post.story_id)
    if post.status != "active":
        # 내용이 가려진 글에는 투표할 수 없음 (D-82와 같은 이유)
        raise api_error(409, "VOTE_NOT_ALLOWED", "지금은 투표할 수 없는 글이에요")
    if post.author_id == user.id:
        raise api_error(403, "SELF_VOTE", "자기 글에는 투표할 수 없어요")
    return post
