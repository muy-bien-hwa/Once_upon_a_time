"""마이페이지·작가 화면 (docs 07 #34~#37, D-95)

- 내 화면: 지운 문장·접힌 문장도 목록에 넣되 **본문은 비워서** 보냄 (약관 26조)
- 작가 화면: 보이는 문장만 / 가입 날짜는 연월까지만
- 숫자(문장 수·이야기 수·받은 추천)는 그 화면의 목록과 **같은 범위**로 셈 → 숫자와 목록이 어긋나지 않음
"""

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session, aliased

from app.errors import api_error
from app.models import Sentence, SentenceVote, Story, User
from app.schemas.profile import (
    AuthorOut,
    MeSummaryOut,
    ProfileSentenceListOut,
    ProfileSentenceOut,
    ProfileSort,
)
from app.timeutil import KST

# 내 화면에 넣는 문장 / 작가 화면에 넣는 문장
MINE = ("active", "folded", "deleted")
PUBLIC = ("active",)

_root = aliased(Sentence)
_story_join = (Story, Sentence.story_id == Story.id)

_up_count = (
    select(func.count())
    .where(SentenceVote.sentence_id == Sentence.id, SentenceVote.value == 1)
    .scalar_subquery()
)

_SORTS = {
    "latest": (Sentence.created_at.desc(), Sentence.id.desc()),
    "votes": (_up_count.desc(), Sentence.created_at.desc(), Sentence.id.desc()),
}


def summary(db: Session, user: User) -> MeSummaryOut:
    """마이페이지 맨 위 칸 (#34)"""
    total, live, stories, ups = _stats(db, user.id, MINE)
    return MeSummaryOut(
        joined_at=user.created_at,
        sentence_count=total,
        story_count=stories,
        received_up_count=ups,
        live_sentence_count=live,
    )


def author(db: Session, nickname: str) -> AuthorOut:
    """작가 화면 맨 위 칸 (#36)"""
    found = find_author(db, nickname)
    total, _live, stories, ups = _stats(db, found.id, PUBLIC)
    return AuthorOut(
        nickname=nickname,
        # DB에는 UTC로 저장 → 한국 시간 기준의 연월 (docs 05)
        joined_month=found.created_at.astimezone(KST).strftime("%Y-%m"),
        sentence_count=total,
        story_count=stories,
        received_up_count=ups,
    )


def find_author(db: Session, nickname: str) -> User:
    """닉네임으로 작가 찾기

    탈퇴한 사람은 닉네임이 비어 있어 애초에 걸리지 않음 → 없는 닉네임과 똑같이 404가 되고,
    그래서 "그 사람이 탈퇴했다"는 사실이 밖으로 새지 않음
    """
    found = db.scalar(select(User).where(User.nickname == nickname, User.deleted_at.is_(None)))
    if found is None:
        raise api_error(404, "USER_NOT_FOUND", "없는 작가예요")
    return found


def my_sentences(
    db: Session, user: User, page: int, size: int, sort: ProfileSort, q: str | None
) -> ProfileSentenceListOut:
    """내가 쓴 문장 (#35)"""
    return _page(db, user.id, MINE, page, size, sort, q)


def author_sentences(
    db: Session, nickname: str, page: int, size: int, sort: ProfileSort, q: str | None
) -> ProfileSentenceListOut:
    """그 작가가 쓴, 지금 보이는 문장 (#37)"""
    return _page(db, find_author(db, nickname).id, PUBLIC, page, size, sort, q)


def _page(
    db: Session,
    author_id: int,
    statuses: tuple[str, ...],
    page: int,
    size: int,
    sort: ProfileSort,
    q: str | None,
) -> ProfileSentenceListOut:
    where = _where(author_id, statuses, q)
    total = db.scalar(select(func.count()).select_from(Sentence).join(*_story_join).where(*where))
    rows = db.execute(
        select(Sentence, Story.title, _up_count)
        .join(*_story_join)
        .where(*where)
        .order_by(*_SORTS[sort])
        .offset((page - 1) * size)
        .limit(size)
    )
    return ProfileSentenceListOut(
        items=[_to_out(row) for row in rows], page=page, size=size, total=total
    )


def _where(author_id: int, statuses: tuple[str, ...], q: str | None = None):
    conditions = [
        Sentence.author_id == author_id,
        Sentence.status.in_(statuses),
        # 스토리째 숨겨졌으면(첫 문장이 removed) 그 안의 문장도 없는 것으로 봄 (docs 05)
        select(_root.id)
        .where(_root.story_id == Story.id, _root.parent_id.is_(None), _root.status != "removed")
        .exists(),
    ]
    if q:
        # 가려진 문장은 본문을 보내지 않으므로 찾을 수도 없어야 함
        conditions += [Sentence.status == "active", Sentence.content.ilike(_like(q), escape="\\")]
    return conditions


def _like(text: str) -> str:
    """찾는 글자 그대로 찾기 — %나 _를 쳐도 '아무 글자'로 해석되지 않게"""
    for letter in ("\\", "%", "_"):
        text = text.replace(letter, "\\" + letter)
    return f"%{text}%"


def _stats(db: Session, author_id: int, statuses: tuple[str, ...]) -> tuple[int, int, int, int]:
    """(문장 수, 그중 보이는 문장 수, 이야기 수, 받은 추천 수)"""
    where = _where(author_id, statuses)
    total, live, stories = db.execute(
        select(
            func.count(Sentence.id),
            func.count(Sentence.id).filter(Sentence.status == "active"),
            func.count(func.distinct(Sentence.story_id)),
        )
        .select_from(Sentence)
        .join(*_story_join)
        .where(*where)
    ).one()
    ups = db.scalar(
        select(func.count())
        .select_from(SentenceVote)
        .join(Sentence, Sentence.id == SentenceVote.sentence_id)
        .join(*_story_join)
        .where(SentenceVote.value == 1, *where)
    )
    return total, live, stories, ups


def _to_out(row: Row) -> ProfileSentenceOut:
    sentence, title, ups = row
    # 지운 문장·접힌 문장은 본문을 보내지 않음 (내 화면에서도)
    hidden = sentence.status in ("deleted", "folded")
    return ProfileSentenceOut(
        id=sentence.id,
        content=None if hidden else sentence.content,
        status=sentence.status,
        story_id=sentence.story_id,
        story_title=title,
        created_at=sentence.created_at,
        up_count=ups,
    )
