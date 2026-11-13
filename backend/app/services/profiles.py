"""마이페이지·작가 화면 (docs 07 #34~#37, D-95)

- 내 화면: 지운 문장·접힌 문장도 목록에 넣되 **본문은 비워서** 보냄 (약관 26조)
- 내 화면은 상태로 거를 수 있고, 검색도 가려진 문장까지 함께 찾음 (내가 쓴 내 문장이므로)
- 작가 화면: 보이는 문장만 / 가입 날짜는 연월까지만
- 숫자(문장 수·이야기 수·받은 추천)는 그 화면의 목록과 **같은 범위**로 셈 → 숫자와 목록이 어긋나지 않음
- 레벨은 예외: 두 화면 모두 "내 문장" 범위로 셈 (score_where 설명 참고, D-100)
"""

from sqlalchemy import Row, func, literal, select
from sqlalchemy.orm import Session, aliased

from app.errors import api_error
from app.models import Sentence, SentenceVote, Story, User
from app.schemas.profile import (
    AuthorOut,
    MeSummaryOut,
    ProfileCounts,
    ProfileFilter,
    ProfileSentenceListOut,
    ProfileSentenceOut,
    ProfileSort,
    ScoreEventOut,
    ScoreHistoryOut,
)
from app.services import levels
from app.timeutil import KST

# 내 화면에 넣는 문장 / 작가 화면에 넣는 문장
MINE = ("active", "folded", "deleted")
PUBLIC = ("active",)

# 본문을 보내지 않는 상태 (약관 26조)
HIDDEN = ("deleted", "folded")

# 내 화면의 거르개 버튼이 고르는 상태
FILTERS: dict[str, tuple[str, ...]] = {
    "all": MINE,
    "active": ("active",),
    "deleted": ("deleted",),
    "folded": ("folded",),
}

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
        # 레벨도 이 범위(지운 것·접힌 것까지)에서 나온 수로 셈 → 지워도 내려가지 않음 (D-100)
        **levels.standing(total, ups),
    )


def author(db: Session, nickname: str) -> AuthorOut:
    """작가 화면 맨 위 칸 (#36)"""
    found = find_author(db, nickname)
    total, _live, stories, ups = _stats(db, found.id, PUBLIC)
    # 레벨만 내 화면과 같은 범위로 다시 셈 → 누가 봐도 같은 레벨 (D-100)
    # 그래서 지운 문장이 있는 사람은 아래 sentence_count보다 점수가 높을 수 있음 — 일부러 그렇게 둠
    mine_total, _mine_live, _mine_stories, mine_ups = _stats(db, found.id, MINE)
    return AuthorOut(
        nickname=nickname,
        # DB에는 UTC로 저장 → 한국 시간 기준의 연월 (docs 05)
        joined_month=found.created_at.astimezone(KST).strftime("%Y-%m"),
        sentence_count=total,
        story_count=stories,
        received_up_count=ups,
        **levels.standing(mine_total, mine_ups),
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
    db: Session,
    user: User,
    page: int,
    size: int,
    sort: ProfileSort,
    q: str | None,
    status: ProfileFilter = "all",
) -> ProfileSentenceListOut:
    """내가 쓴 문장 (#35). 상태로 거를 수 있고, 거르개 버튼에 적을 수도 함께 보냄"""
    listing = _page(db, user.id, FILTERS[status], page, size, sort, q)
    listing.counts = _counts(db, user.id, q)
    return listing


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


def score_where(author_id: int | None = None):
    """점수를 세는 범위 (D-100)

    마이페이지·작가 화면·점수 내역·레벨 분포가 **모두** 이 조건을 쓴다 → 네 곳의 숫자가 어긋날 수 없다.
    author_id를 주지 않으면 작가를 가리지 않음 (레벨 분포처럼 모두를 한 번에 셀 때)
    """
    return _where(author_id, MINE)


def _where(author_id: int | None, statuses: tuple[str, ...], q: str | None = None):
    conditions = [
        Sentence.status.in_(statuses),
        # 스토리째 숨겨졌으면(첫 문장이 removed) 그 안의 문장도 없는 것으로 봄 (docs 05)
        select(_root.id)
        .where(_root.story_id == Story.id, _root.parent_id.is_(None), _root.status != "removed")
        .exists(),
    ]
    if author_id is not None:
        conditions.append(Sentence.author_id == author_id)
    if q:
        # 가려진 문장도 함께 찾음 — 내가 쓴 내 문장이므로 (본문은 여전히 보내지 않음)
        conditions.append(Sentence.content.ilike(like_pattern(q), escape="\\"))
    return conditions


def like_pattern(text: str) -> str:
    """찾는 글자 그대로 찾기 — %나 _를 쳐도 '아무 글자'로 해석되지 않게"""
    for letter in ("\\", "%", "_"):
        text = text.replace(letter, "\\" + letter)
    return f"%{text}%"


def _counts(db: Session, author_id: int, q: str | None) -> ProfileCounts:
    """거르개 버튼에 적을 수 (검색 중이면 그 검색 안에서)"""
    rows = db.execute(
        select(Sentence.status, func.count())
        .select_from(Sentence)
        .join(*_story_join)
        .where(*_where(author_id, MINE, q))
        .group_by(Sentence.status)
    ).all()
    found = dict(rows)
    return ProfileCounts(
        all=sum(found.values()),
        active=found.get("active", 0),
        deleted=found.get("deleted", 0),
        folded=found.get("folded", 0),
    )


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


def score_history(db: Session, user: User, page: int, size: int) -> ScoreHistoryOut:
    """점수가 어디서 왔는지 (D-100)

    점수에 들어간 문장과 똑같은 범위(score_where)에서 뽑으므로, 내역을 다 더하면 점수가 된다
    """
    events = _events(user.id)
    total = db.scalar(select(func.count()).select_from(events))
    rows = db.execute(
        select(events)
        .order_by(
            events.c.at.desc(),
            # 같은 시각에 들어온 일끼리도 순서가 흔들리지 않게 (쪽을 넘겨도 빠지거나 겹치지 않음)
            events.c.sentence_id.desc(),
            events.c.kind,
            events.c.actor_id,
        )
        .offset((page - 1) * size)
        .limit(size)
    )
    return ScoreHistoryOut(
        items=[_to_event(row) for row in rows], page=page, size=size, total=total
    )


def _events(author_id: int):
    """점수가 생긴 일 두 가지(문장을 씀 / 추천을 받음)를 한 표로 이어 붙임

    점수는 "문장 × 10 + 추천 × 1"이므로, 문장 한 줄과 추천 한 줄이 곧 점수 한 덩이가 된다
    """
    where = score_where(author_id)
    wrote = (
        select(
            literal("sentence").label("kind"),
            literal(levels.SENTENCE_POINTS).label("points"),
            Sentence.created_at.label("at"),
            Story.id.label("story_id"),
            Story.title.label("story_title"),
            Sentence.id.label("sentence_id"),
            Sentence.content.label("content"),
            Sentence.status.label("status"),
            # 순서를 고정할 때만 쓰는 열: 그 일을 만든 사람 (문장은 쓴 사람, 추천은 누른 사람)
            Sentence.author_id.label("actor_id"),
        )
        .select_from(Sentence)
        .join(*_story_join)
        .where(*where)
    )
    received = (
        select(
            literal("up"),
            literal(levels.UP_POINTS),
            SentenceVote.created_at,
            Story.id,
            Story.title,
            Sentence.id,
            Sentence.content,
            Sentence.status,
            SentenceVote.user_id,
        )
        .select_from(SentenceVote)
        .join(Sentence, Sentence.id == SentenceVote.sentence_id)
        .join(*_story_join)
        # 비추천은 점수를 깎지 않으므로 내역에도 넣지 않음 (D-100)
        .where(SentenceVote.value == 1, *where)
    )
    return wrote.union_all(received).subquery()


def _to_event(row: Row) -> ScoreEventOut:
    return ScoreEventOut(
        kind=row.kind,
        points=row.points,
        at=row.at,
        story_id=row.story_id,
        story_title=row.story_title,
        sentence_id=row.sentence_id,
        # 지운 문장·접힌 문장은 본문을 보내지 않음 (내 화면에서도)
        sentence_content=None if row.status in HIDDEN else row.content,
    )


def _to_out(row: Row) -> ProfileSentenceOut:
    sentence, title, ups = row
    # 지운 문장·접힌 문장은 본문을 보내지 않음 (내 화면에서도)
    hidden = sentence.status in HIDDEN
    return ProfileSentenceOut(
        id=sentence.id,
        content=None if hidden else sentence.content,
        status=sentence.status,
        story_id=sentence.story_id,
        story_title=title,
        created_at=sentence.created_at,
        up_count=ups,
    )
