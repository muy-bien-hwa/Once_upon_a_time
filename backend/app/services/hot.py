"""홈 Hot 영역: 기간별 추천 Top (docs 07 #10·#11, D-76)

기간은 한국 시간 기준 (D-16): 일간 = 오늘 0시부터 / 주간 = 오늘 포함 7일 / 월간 = 오늘 포함 30일
기간 3개를 각각 조회하지 않고, 월간 범위를 한 번 읽으면서 기간별 합계를 함께 구함
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from app.models import Sentence, SentenceVote, StoryRecommendation
from app.schemas.sentence import StoryRef
from app.schemas.stats import HotPeriod, HotSentence, HotSentences, HotStories, HotStory
from app.services.sentences import fetch_sentences
from app.services.stories import list_stories_by_ids
from app.timeutil import kst_today_start

TOP_LIMIT = 5
# 기간 이름 → 오늘을 포함해 며칠치인지 (순서 = 조회 결과의 열 순서)
_DAYS: dict[HotPeriod, int] = {"day": 1, "week": 7, "month": 30}


def period_start(period: HotPeriod) -> datetime:
    """그 기간의 시작 시각 (한국 시간 0시 기준)"""
    return kst_today_start() - timedelta(days=_DAYS[period] - 1)


def top_stories(db: Session) -> HotStories:
    """추천을 많이 받은 스토리 Top 5 (일간·주간·월간)"""
    counted = func.count()
    rows = db.execute(
        select(
            StoryRecommendation.story_id,
            counted.filter(StoryRecommendation.created_at >= period_start("day")).label("day"),
            counted.filter(StoryRecommendation.created_at >= period_start("week")).label("week"),
            counted.label("month"),
        )
        .where(StoryRecommendation.created_at >= period_start("month"))
        .group_by(StoryRecommendation.story_id)
    ).all()

    result: dict[str, list[HotStory]] = {}
    for column, period in enumerate(_DAYS, start=1):
        counts = dict(_pick_top(rows, column))
        # 숨겨진 스토리(첫 문장이 removed)는 list_stories_by_ids에서 빠짐
        stories = list_stories_by_ids(db, list(counts))
        result[period] = [
            HotStory(story=story, recommend_count=counts[story.id]) for story in stories
        ]
    return HotStories(**result)


def top_sentences(db: Session) -> HotSentences:
    """추천(추천 − 비추천)을 많이 받은 문장 Top 5 (일간·주간·월간)"""
    total = func.sum(SentenceVote.value)
    rows = db.execute(
        select(
            SentenceVote.sentence_id,
            total.filter(SentenceVote.created_at >= period_start("day")).label("day"),
            total.filter(SentenceVote.created_at >= period_start("week")).label("week"),
            total.label("month"),
        )
        .where(SentenceVote.created_at >= period_start("month"))
        .group_by(SentenceVote.sentence_id)
    ).all()

    picks = {period: _pick_top(rows, column) for column, period in enumerate(_DAYS, start=1)}
    ids = {sentence_id for top in picks.values() for sentence_id, _ in top}
    # 접힘·삭제된 문장은 내용을 보여줄 수 없으므로 뺌 (D-63·D-69)
    found = {
        sentence.id: sentence
        for sentence in fetch_sentences(db, Sentence.id.in_(ids), Sentence.status == "active")
    }
    # 숨겨진 스토리의 문장도 뺌 → 목록에 없는 스토리가 Hot에만 뜨지 않도록
    titles = {
        story.id: story.title
        for story in list_stories_by_ids(db, [s.story_id for s in found.values()])
    }

    result: dict[str, list[HotSentence]] = {}
    for period, top in picks.items():
        items = []
        for sentence_id, score in top:
            sentence = found.get(sentence_id)
            if sentence is None or sentence.story_id not in titles:
                continue
            items.append(
                HotSentence(
                    sentence=sentence,
                    story=StoryRef(id=sentence.story_id, title=titles[sentence.story_id]),
                    vote_count=score,
                )
            )
        result[period] = items
    return HotSentences(**result)


def _pick_top(rows: Sequence[Row], column: int) -> list[tuple[int, int]]:
    """(id, 점수) 중 점수가 1 이상인 것만 높은 순으로 최대 5개 (같으면 먼저 만들어진 것)"""
    scored = [(row[0], int(row[column] or 0)) for row in rows]
    positive = [item for item in scored if item[1] > 0]
    positive.sort(key=lambda item: (-item[1], item[0]))
    return positive[:TOP_LIMIT]
