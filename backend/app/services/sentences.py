"""문장 조회·이어 쓰기: 개수 붙이기, status 처리, 정렬, 경로 (docs 04·07)"""

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, aliased

from app.config import settings
from app.errors import api_error
from app.models import Sentence, SentenceVote, Story, User
from app.schemas.sentence import PathOut, SentenceOut, SentenceSort, StoryRef
from app.services.ranking import rank_score
from app.timeutil import kst_now

_child = aliased(Sentence)

# 문장마다 붙이는 개수 (저장하지 않고 조회할 때 계산, docs 05 "캐시 컬럼 없음")
_up_count = (
    select(func.count())
    .where(SentenceVote.sentence_id == Sentence.id, SentenceVote.value == 1)
    .scalar_subquery()
)
_down_count = (
    select(func.count())
    .where(SentenceVote.sentence_id == Sentence.id, SentenceVote.value == -1)
    .scalar_subquery()
)
_child_count = (
    select(func.count())
    .select_from(_child)
    .where(_child.parent_id == Sentence.id, _child.status != "removed")
    .scalar_subquery()
)


def fetch_sentences(db: Session, *conditions: ColumnElement[bool]) -> list[SentenceOut]:
    """조건에 맞는 문장들을 개수 정보와 함께 가져옴 (removed는 항상 뺌)"""
    stmt = (
        select(Sentence, User.nickname, _up_count, _down_count, _child_count)
        .join(User, User.id == Sentence.author_id)
        .where(Sentence.status != "removed", *conditions)
    )
    return [
        _to_out(sentence, nickname, up, down, children)
        for sentence, nickname, up, down, children in db.execute(stmt)
    ]


def get_sentence(db: Session, sentence_id: int) -> SentenceOut:
    """문장 1개. 없거나 숨김(removed)이면 404"""
    items = fetch_sentences(db, Sentence.id == sentence_id)
    if not items:
        raise _not_found()
    return items[0]


def get_path(db: Session, sentence_id: int) -> PathOut:
    """첫 문장부터 이 문장까지 (#6)

    재귀 CTE: 이 문장에서 시작해 부모를 따라 첫 문장까지 올라가며 id를 모음
    """
    path = (
        select(Sentence.id, Sentence.parent_id)
        .where(Sentence.id == sentence_id)
        .cte("path", recursive=True)
    )
    path = path.union_all(
        select(Sentence.id, Sentence.parent_id).join(path, Sentence.id == path.c.parent_id)
    )
    ids = db.scalars(select(path.c.id)).all()
    items = sorted(fetch_sentences(db, Sentence.id.in_(ids)), key=lambda s: s.depth)
    # 없는 문장이거나, 경로 중간에 숨김(removed) 문장이 있으면 404
    if not ids or len(items) != len(ids):
        raise _not_found()
    story = db.get(Story, items[0].story_id)
    return PathOut(story=StoryRef(id=story.id, title=story.title), items=items)


def list_children(
    db: Session, parent_id: int, sort: SentenceSort, user_id: int | None
) -> list[SentenceOut]:
    """이어진 문장들 (#7). 삭제·접힌 문장 아래의 이어진 문장도 볼 수 있음 (D-69)"""
    get_sentence(db, parent_id)  # 없거나 숨김이면 404
    return order_sentences(fetch_sentences(db, Sentence.parent_id == parent_id), sort, user_id)


def add_child(db: Session, user: User, parent_id: int, content: str) -> SentenceOut:
    """이어 쓰기 (#8)"""
    # 부모 문장을 잠그고 읽음 → 판단하는 동안 다른 요청(삭제·신고)이 끼어들지 못함
    parent = db.scalar(select(Sentence).where(Sentence.id == parent_id).with_for_update())
    if parent is None or parent.status == "removed":
        raise _not_found()
    if parent.status == "deleted":
        raise api_error(409, "PARENT_DELETED", "삭제된 문장 뒤에는 이어 쓸 수 없어요")
    if parent.status == "folded":
        raise api_error(409, "PARENT_FOLDED", "신고 처리된 문장 뒤에는 이어 쓸 수 없어요")

    # 스토리와 깊이는 요청으로 받지 않고 부모에서 계산 → 어긋날 수 없음
    child = Sentence(
        story_id=parent.story_id,
        parent_id=parent.id,
        author_id=user.id,
        content=content,
        depth=parent.depth + 1,
    )
    db.add(child)
    db.commit()
    return get_sentence(db, child.id)


def order_sentences(
    items: list[SentenceOut], sort: SentenceSort, user_id: int | None
) -> list[SentenceOut]:
    """보통 문장은 sort 기준으로 높은 것이 위 / 접힘·삭제된 문장은 맨 아래에 작성순 (04 규칙 2)"""
    normal = [s for s in items if s.status == "active"]
    bottom = sorted((s for s in items if s.status != "active"), key=lambda s: (s.created_at, s.id))
    return sorted(normal, key=_sort_key(sort, user_id), reverse=True) + bottom


def _sort_key(sort: SentenceSort, user_id: int | None) -> Callable[[SentenceOut], tuple]:
    if sort == "latest":
        return lambda s: (s.created_at, s.id)
    if sort == "votes":
        # 추천순 = 추천 − 비추천 (D-64), 같으면 최신순
        return lambda s: (s.up_count - s.down_count, s.created_at, s.id)

    # score: 투표 + 최신성 + 흔들기 (docs 04)
    now = datetime.now(UTC)
    kst_date = kst_now().date().isoformat()
    return lambda s: (
        rank_score(
            up=s.up_count,
            down=s.down_count,
            age_hours=max((now - s.created_at).total_seconds() / 3600, 0),
            user_id=user_id,
            sentence_id=s.id,
            kst_date=kst_date,
            b=settings.sentence_rank_b,
            h=settings.sentence_rank_h,
            j0=settings.sentence_rank_j0,
        ),
        s.id,
    )


def _to_out(sentence: Sentence, nickname: str, up: int, down: int, children: int) -> SentenceOut:
    # 삭제된 문장·신고로 접힌 문장은 본문과 작성자를 보내지 않음 → 화면엔 문구만 (D-63·D-69)
    hidden = sentence.status in ("deleted", "folded")
    return SentenceOut(
        id=sentence.id,
        story_id=sentence.story_id,
        parent_id=sentence.parent_id,
        depth=sentence.depth,
        content=None if hidden else sentence.content,
        status=sentence.status,
        author_nickname=None if hidden else nickname,
        created_at=sentence.created_at,
        up_count=up,
        down_count=down,
        child_count=children,
    )


def _not_found():
    return api_error(404, "SENTENCE_NOT_FOUND", "없거나 사라진 문장이에요")
