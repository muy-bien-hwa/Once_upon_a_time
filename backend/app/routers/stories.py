"""스토리 API 주소 (docs 07 #1~#3, 추천 #12·#13)"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentAuthor, CurrentUser, DbSession, OptionalUser
from app.schemas.story import (
    StoryAuthorsOut,
    StoryCreate,
    StoryCreateOut,
    StoryListOut,
    StoryOut,
    StorySort,
)
from app.services import managers as manager_service
from app.services import recommendations as recommendation_service
from app.services import stories as story_service

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("")
def list_stories(
    db: DbSession,
    user: OptionalUser,
    sort: StorySort = "latest",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> StoryListOut:
    """스토리 목록 (#1). 로그인했으면 내가 추천한 스토리도 함께"""
    return story_service.list_stories(db, sort, page, size, user_id=user.id if user else None)


@router.post("", status_code=201)
def create_story(data: StoryCreate, db: DbSession, user: CurrentAuthor) -> StoryCreateOut:
    """새 스토리: 제목 + 첫 문장 (#2)"""
    return story_service.create_story(db, user, data)


@router.get("/{story_id}")
def get_story(story_id: int, db: DbSession, user: OptionalUser) -> StoryOut:
    """스토리 하나 (#3)"""
    return story_service.get_story(db, story_id, user_id=user.id if user else None)


@router.put("/{story_id}/recommendation")
def add_recommendation(story_id: int, db: DbSession, user: CurrentUser) -> StoryOut:
    """추천 누르기 (F-13)"""
    return recommendation_service.add_recommendation(db, user, story_id)


@router.delete("/{story_id}/recommendation")
def remove_recommendation(story_id: int, db: DbSession, user: CurrentUser) -> StoryOut:
    """내 추천 취소 (F-13)"""
    return recommendation_service.remove_recommendation(db, user, story_id)


@router.get("/{story_id}/authors")
def list_authors(story_id: int, db: DbSession, user: OptionalUser) -> StoryAuthorsOut:
    """스토리 작가 목록 (누구나 볼 수 있음) + 내가 할 수 있는 일 (D-91)"""
    return manager_service.list_authors(db, story_id, user_id=user.id if user else None)


@router.put("/{story_id}/managers/{user_id}")
def appoint_manager(
    story_id: int, user_id: int, db: DbSession, user: CurrentUser
) -> StoryAuthorsOut:
    """관리자로 임명 (스토리를 시작한 작가만)"""
    return manager_service.appoint(db, user, story_id, user_id)


@router.delete("/{story_id}/managers/{user_id}")
def dismiss_manager(
    story_id: int, user_id: int, db: DbSession, user: CurrentUser
) -> StoryAuthorsOut:
    """관리자 권한 거두기"""
    return manager_service.dismiss(db, user, story_id, user_id)
