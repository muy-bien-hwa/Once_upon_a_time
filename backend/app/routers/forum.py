"""포럼 API 주소 (docs 07 포럼, F-17)

글 목록·쓰기는 스토리 밑(`/api/stories/{id}/forum/posts`),
글 하나는 스토리와 상관없이 번호로(`/api/forum/posts/{id}`)
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentAuthor, CurrentUser, DbSession, OptionalUser
from app.schemas.forum import PostCreate, PostListOut, PostOut, PostSort
from app.services import forum as forum_service

router = APIRouter(tags=["forum"])


@router.get("/api/stories/{story_id}/forum/posts")
def list_posts(
    story_id: int,
    db: DbSession,
    user: OptionalUser,
    sort: PostSort = "new",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> PostListOut:
    """스토리의 글 목록 (고정글 먼저, 그다음 new·hot)"""
    return forum_service.list_posts(
        db, story_id, sort, page, size, user_id=user.id if user else None
    )


@router.post("/api/stories/{story_id}/forum/posts", status_code=201)
def create_post(story_id: int, data: PostCreate, db: DbSession, user: CurrentAuthor) -> PostOut:
    """글 쓰기 (로그인 + 닉네임, D-29)"""
    return forum_service.create_post(db, user, story_id, data)


@router.get("/api/forum/posts/{post_id}")
def get_post(post_id: int, db: DbSession, user: OptionalUser) -> PostOut:
    """글 하나"""
    return forum_service.get_post(db, post_id, user_id=user.id if user else None)


@router.delete("/api/forum/posts/{post_id}")
def delete_post(post_id: int, db: DbSession, user: CurrentUser) -> dict[str, str]:
    """내 글 삭제 (댓글도 함께 사라짐, D-91)"""
    forum_service.delete_post(db, user, post_id)
    return {"status": "deleted"}
