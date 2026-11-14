"""레벨 분포·여러 사람의 레벨 (D-100)

/levels 화면은 로그인 없이 누구나 봄 → 단계마다 몇 명인지만 보내고, 누가 몇 단계인지는 보내지 않음.
한 사람씩 조회하면 사람 수만큼 쿼리가 늘어나므로, 작가별 합계를 SQL에서 두 번에 묶고
레벨 계산만 파이썬에서 함 (레벨 규칙은 levels.py 한 곳에만 두어야 하므로)
"""

from collections import Counter
from collections.abc import Iterable

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Sentence, SentenceVote, Story, User
from app.schemas.level import LevelCountOut, LevelDistributionOut
from app.services import levels
from app.services.profiles import score_where

# 셀 사람: 닉네임이 있고 탈퇴하지 않은 사람 (find_author가 "있는 작가"로 보는 기준과 같음)
WRITER = (User.nickname.is_not(None), User.deleted_at.is_(None))

# 점수의 두 재료 — 작가별로 쓴 문장 수 / 받은 추천 수 (D-100)
# 여기 두 개를 아래 두 함수가 함께 써야 "분포에서 본 레벨"과 "글 옆의 레벨"이 어긋날 수 없다
_WRITTEN = select(Sentence.author_id, func.count(Sentence.id))
_RECEIVED = (
    select(Sentence.author_id, func.count())
    .select_from(SentenceVote)
    .join(Sentence, Sentence.id == SentenceVote.sentence_id)
    .where(SentenceVote.value == 1)
)


def distribution(db: Session) -> LevelDistributionOut:
    """단계마다 몇 명인지 — 한 명도 없는 단계는 보내지 않음"""
    written = _per_author(db, _WRITTEN, *WRITER)
    received = _per_author(db, _RECEIVED, *WRITER)

    found: Counter[int] = Counter()
    # 문장이 하나도 없는 사람은 0단계라 written에 애초에 없음 (문장 없이 추천만 받을 수는 없으므로)
    for author_id, sentence_count in written.items():
        level = levels.level_of(levels.score(sentence_count, received.get(author_id, 0)))
        if level >= 1:
            found[level] += 1

    return LevelDistributionOut(
        items=[
            LevelCountOut(level=level, name=levels.name_of(level), count=found[level])
            for level in sorted(found)
        ],
        total_writers=sum(found.values()),
    )


def levels_of(db: Session, author_ids: Iterable[int]) -> dict[int, dict]:
    """여러 사람의 레벨을 한 번에 — levels.standing()이 주는 묶음을 사람 번호별로 (D-100)

    커뮤니티 글·댓글 옆에 작성자 레벨을 붙일 때 씀. 한 줄씩 물으면 글 수만큼 쿼리가 늘어나므로
    distribution()과 똑같이 두 번으로 묶는다. 세는 범위도 같은 score_where()라서
    여기서 보이는 레벨은 /api/me/summary·/api/users/{nickname}이 말하는 레벨과 늘 같다.

    탈퇴한 사람은 빼지 않음 — 탈퇴해도 그때 쓴 글이 사라지지는 않으므로 (D-95).
    그래서 WRITER 조건을 쓰지 않는다 (분포는 "지금 있는 작가"를 세는 것이라 거기서만 씀)
    """
    wanted = set(author_ids)
    if not wanted:
        # 물어볼 사람이 없으면 DB를 건드리지 않음 (글이 하나도 없는 목록)
        return {}

    mine = Sentence.author_id.in_(wanted)
    written = _per_author(db, _WRITTEN, mine)
    received = _per_author(db, _RECEIVED, mine)
    # 세는 범위 안에 문장이 하나도 없는 사람은 written에 없음 → 0단계(레벨 없음)
    return {
        author_id: levels.standing(written.get(author_id, 0), received.get(author_id, 0))
        for author_id in wanted
    }


def _per_author(db: Session, query: Select, *conditions) -> dict[int, int]:
    """작가별 수를 한 번에 — 세는 범위(score_where)는 프로필 화면의 점수와 똑같이"""
    rows = db.execute(
        query.join(Story, Sentence.story_id == Story.id)
        .join(User, User.id == Sentence.author_id)
        .where(*score_where(), *conditions)
        .group_by(Sentence.author_id)
    ).all()
    return dict(rows)
