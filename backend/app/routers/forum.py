"""포럼 API 주소 (docs 07 포럼, F-17)

글 목록·쓰기는 스토리 밑(`/api/stories/{id}/forum/posts`),
글 하나는 스토리와 상관없이 번호로(`/api/forum/posts/{id}`)
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import CurrentAuthor, CurrentUser, DbSession, OptionalUser
from app.schemas.forum import (
    CommentCreate,
    CommentListOut,
    CommentOut,
    PostCreate,
    PostListOut,
    PostOut,
    PostSort,
    VoteCreate,
)
from app.services import forum as forum_service
from app.services import forum_comments as comment_service
from app.services import forum_votes as vote_service

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


@router.get("/api/forum/posts/{post_id}/comments")
def list_comments(post_id: int, db: DbSession) -> CommentListOut:
    """글의 댓글 (맨 위 댓글 + 답글, 화면에서 2단으로 묶음)"""
    return CommentListOut(items=comment_service.list_comments(db, post_id))


@router.post("/api/forum/posts/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int, data: CommentCreate, db: DbSession, user: CurrentAuthor
) -> CommentOut:
    """댓글·답글 쓰기 (답글의 답글도 같은 줄에 붙음, D-91)"""
    return comment_service.create_comment(db, user, post_id, data)


@router.delete("/api/forum/comments/{comment_id}")
def delete_comment(comment_id: int, db: DbSession, user: CurrentUser) -> dict[str, str]:
    """내 댓글 삭제 (맨 위 댓글이면 답글도 함께 사라짐)"""
    comment_service.delete_comment(db, user, comment_id)
    return {"status": "deleted"}


@router.put("/api/forum/posts/{post_id}/vote")
def set_vote(post_id: int, data: VoteCreate, db: DbSession, user: CurrentUser) -> PostOut:
    """글에 추천·비추천 누르기"""
    return vote_service.set_vote(db, user, post_id, data.value)


@router.delete("/api/forum/posts/{post_id}/vote")
def clear_vote(post_id: int, db: DbSession, user: CurrentUser) -> PostOut:
    """내 표 취소"""
    return vote_service.clear_vote(db, user, post_id)


@router.put("/api/forum/posts/{post_id}/pin")
def pin_post(post_id: int, db: DbSession, user: CurrentUser) -> PostOut:
    """글 고정 (스토리를 시작한 작가·관리자만, D-91)"""
    return forum_service.pin_post(db, user, post_id)


@router.delete("/api/forum/posts/{post_id}/pin")
def unpin_post(post_id: int, db: DbSession, user: CurrentUser) -> PostOut:
    """고정 해제"""
    return forum_service.unpin_post(db, user, post_id)
