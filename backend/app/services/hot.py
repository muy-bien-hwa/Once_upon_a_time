"""홈 Hot 영역: 기간별 추천 Top (docs 07 #10·#11, D-76)

기간은 한국 시간 기준 (D-16): 일간 = 오늘 0시부터 / 주간 = 오늘 포함 7일 / 월간 = 오늘 포함 30일
"""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Sentence, SentenceVote, Story, StoryRecommendation
from app.schemas.sentence import StoryRef
from app.schemas.stats import HotPeriod, HotSentence, HotSentences, HotStories, HotStory
from app.services.sentences import fetch_sentences
from app.services.stories import list_stories_by_ids
from app.timeutil import kst_today_start

TOP_LIMIT = 5
_DAYS = {"day": 1, "week": 7, "month": 30}


def period_start(period: HotPeriod) -> datetime:
    return kst_today_start() - timedelta(days=_DAYS[period] - 1)


def top_stories(db: Session) -> HotStories:
    return HotStories(**{period: _top_stories(db, period) for period in _DAYS})


def top_sentences(db: Session) -> HotSentences:
    return HotSentences(**{period: _top_sentences(db, period) for period in _DAYS})


def _top_stories(db: Session, period: HotPeriod) -> list[HotStory]:
    """기간 안에 받은 추천이 많은 스토리 순"""
    count = func.count().label("count")
    rows = db.execute(
        select(StoryRecommendation.story_id, count)
        .where(StoryRecommendation.created_at >= period_start(period))
        .group_by(StoryRecommendation.story_id)
        .order_by(count.desc(), StoryRecommendation.story_id)
        .limit(TOP_LIMIT)
    ).all()

    counts = dict(rows)
    stories = list_stories_by_ids(db, list(counts))
    return [HotStory(story=story, recommend_count=counts[story.id]) for story in stories]


def _top_sentences(db: Session, period: HotPeriod) -> list[HotSentence]:
    """기간 안에 받은 추천(추천 − 비추천)이 많은 문장 순"""
    score = func.sum(SentenceVote.value).label("score")
    rows = db.execute(
        select(SentenceVote.sentence_id, score)
        .where(SentenceVote.created_at >= period_start(period))
        .group_by(SentenceVote.sentence_id)
        .order_by(score.desc(), SentenceVote.sentence_id)
        .limit(TOP_LIMIT)
    ).all()

    scores = dict(rows)
    # 접힘·삭제된 문장은 내용을 못 보여주므로 뺌 (D-63·D-69)
    sentences = fetch_sentences(db, Sentence.id.in_(list(scores)), Sentence.status == "active")
    titles = dict(
        db.execute(
            select(Story.id, Story.title).where(
                Story.id.in_({sentence.story_id for sentence in sentences})
            )
        ).all()
    )
    sentences.sort(key=lambda sentence: (-scores[sentence.id], sentence.id))
    return [
        HotSentence(
            sentence=sentence,
            story=StoryRef(id=sentence.story_id, title=titles[sentence.story_id]),
            vote_count=scores[sentence.id],
        )
        for sentence in sentences
    ]
