"""기록 API 주소 (docs 07 #9)"""

from fastapi import APIRouter

from app.deps import DbSession
from app.schemas.stats import HotSentences, HotStories, RecordOut
from app.services import hot as hot_service
from app.services import stories as story_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/record")
def get_record(db: DbSession) -> RecordOut:
    """지금까지 기록: 참여 작가가 가장 많은 스토리 (#9)"""
    return RecordOut(most_authors_story=story_service.most_authors_story(db))


@router.get("/top-stories")
def get_top_stories(db: DbSession) -> HotStories:
    """추천 많은 스토리 Top 5 · 일간·주간·월간 (#10)"""
    return hot_service.top_stories(db)


@router.get("/top-sentences")
def get_top_sentences(db: DbSession) -> HotSentences:
    """추천 많은 문장 Top 5 · 일간·주간·월간 (#11)"""
    return hot_service.top_sentences(db)
