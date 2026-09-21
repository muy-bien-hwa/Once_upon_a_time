"""스토리 API 주소 (docs 07 #1~#3)"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentUser, DbSession
from app.schemas.story import StoryCreate, StoryCreateOut, StoryListOut, StoryOut, StorySort
from app.services import stories as story_service

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("")
def list_stories(
    db: DbSession,
    sort: StorySort = "latest",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> StoryListOut:
    """스토리 목록 (#1)"""
    return story_service.list_stories(db, sort, page, size)


@router.post("", status_code=201)
def create_story(data: StoryCreate, db: DbSession, user: CurrentUser) -> StoryCreateOut:
    """새 스토리: 제목 + 첫 문장 (#2)"""
    return story_service.create_story(db, user, data)


@router.get("/{story_id}")
def get_story(story_id: int, db: DbSession) -> StoryOut:
    """스토리 하나 (#3)"""
    return story_service.get_story(db, story_id)
