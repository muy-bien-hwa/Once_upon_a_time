"""레벨 분포 (D-100)

/levels 화면은 로그인 없이 누구나 봄 → 단계마다 몇 명인지만 보내고, 누가 몇 단계인지는 보내지 않음.
한 사람씩 조회하면 사람 수만큼 쿼리가 늘어나므로, 작가별 합계를 SQL에서 두 번에 묶고
레벨 계산만 파이썬에서 함 (레벨 규칙은 levels.py 한 곳에만 두어야 하므로)
"""

from collections import Counter

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models import Sentence, SentenceVote, Story, User
from app.schemas.level import LevelCountOut, LevelDistributionOut
from app.services import levels
from app.services.profiles import score_where

# 셀 사람: 닉네임이 있고 탈퇴하지 않은 사람 (find_author가 "있는 작가"로 보는 기준과 같음)
WRITER = (User.nickname.is_not(None), User.deleted_at.is_(None))


def distribution(db: Session) -> LevelDistributionOut:
    """단계마다 몇 명인지 — 한 명도 없는 단계는 보내지 않음"""
    written = _per_author(db, select(Sentence.author_id, func.count(Sentence.id)))
    received = _per_author(
        db,
        select(Sentence.author_id, func.count())
        .select_from(SentenceVote)
        .join(Sentence, Sentence.id == SentenceVote.sentence_id)
        .where(SentenceVote.value == 1),
    )

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


def _per_author(db: Session, query: Select) -> dict[int, int]:
    """작가별 수를 한 번에 — 세는 범위(score_where)는 프로필 화면의 점수와 똑같이"""
    rows = db.execute(
        query.join(Story, Sentence.story_id == Story.id)
        .join(User, User.id == Sentence.author_id)
        .where(*score_where(), *WRITER)
        .group_by(Sentence.author_id)
    ).all()
    return dict(rows)
