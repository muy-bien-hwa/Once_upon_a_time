"""포럼 댓글 (F-17·D-42·D-91)

- 2단까지만: 답글의 답글도 윗 댓글에 매달아 같은 줄에 놓음
- 누구에게 한 말인지는 사람(reply_to_user_id)으로 저장 → 화면에서 지금 닉네임으로 @표시
- 삭제하면 조용히 사라짐 (맨 위 댓글을 지우면 그 아래 답글도 함께, 글 삭제와 같은 방식)
"""

from sqlalchemy import Row, select, update
from sqlalchemy.orm import Session, aliased

from app.errors import api_error
from app.models import ForumComment, ForumPost, User
from app.schemas.forum import CommentCreate, CommentOut
from app.services import limits
from app.services.forum import post_gone

_author = aliased(User)
_mentioned = aliased(User)


def list_comments(db: Session, post_id: int) -> list[CommentOut]:
    """글의 댓글 전부 (쓴 순서대로). 화면에서 맨 위 댓글 + 답글로 묶음"""
    _readable_post(db, post_id)
    rows = db.execute(_select_comments().where(ForumComment.post_id == post_id)).all()
    return [_to_out(row) for row in sorted(rows, key=lambda r: (r[0].created_at, r[0].id))]


def create_comment(db: Session, user: User, post_id: int, data: CommentCreate) -> CommentOut:
    """댓글·답글 쓰기"""
    _readable_post(db, post_id)
    limits.check_new_comment(db, user)
    parent_id, reply_to_user_id = _resolve_parent(db, post_id, data.parent_id)

    comment = ForumComment(
        post_id=post_id,
        parent_id=parent_id,
        author_id=user.id,
        body=data.body,
        reply_to_user_id=reply_to_user_id,
    )
    db.add(comment)
    db.commit()
    return get_comment(db, comment.id)


def get_comment(db: Session, comment_id: int) -> CommentOut:
    row = db.execute(_select_comments().where(ForumComment.id == comment_id)).first()
    if row is None:
        raise _comment_gone(db, comment_id)
    return _to_out(row)


def delete_comment(db: Session, user: User, comment_id: int) -> None:
    """내 댓글 삭제. 맨 위 댓글이면 그 아래 답글도 함께 사라짐 (D-91)"""
    comment = db.get(ForumComment, comment_id)
    if comment is None or comment.status == "removed":
        raise _comment_gone(db, comment_id)
    if comment.author_id != user.id:
        raise api_error(403, "NOT_MY_COMMENT", "내가 쓴 댓글만 지울 수 있어요")

    comment.status = "removed"
    if comment.parent_id is None:
        db.execute(
            update(ForumComment)
            .where(ForumComment.parent_id == comment.id)
            .values(status="removed")
        )
    db.commit()


def _resolve_parent(
    db: Session, post_id: int, parent_id: int | None
) -> tuple[int | None, int | None]:
    """답글이 매달릴 윗 댓글과 "누구에게 한 말인지"를 정함

    답글에 답글을 달면 한 칸 더 들어가지 않고 **윗 댓글에 나란히** 붙고,
    대신 방금 답한 사람을 @로 부른다 (D-91)
    """
    if parent_id is None:
        return None, None

    parent = db.scalar(
        select(ForumComment).where(ForumComment.id == parent_id, ForumComment.post_id == post_id)
    )
    if parent is None or parent.status == "removed":
        raise api_error(404, "COMMENT_NOT_FOUND", "답글을 달 댓글이 없어요")
    if parent.status != "active":
        raise api_error(409, "COMMENT_NOT_ALLOWED", "지금은 답글을 달 수 없는 댓글이에요")

    return parent.parent_id or parent.id, parent.author_id


def _readable_post(db: Session, post_id: int) -> ForumPost:
    """댓글을 보거나 쓸 수 있는 글인지 (없음·삭제 404)"""
    post = db.get(ForumPost, post_id)
    if post is None or post.status == "removed":
        raise post_gone(db, post_id)
    return post


def _select_comments():
    return (
        select(ForumComment, _author.nickname, _mentioned.nickname)
        .join(_author, _author.id == ForumComment.author_id)
        .outerjoin(_mentioned, _mentioned.id == ForumComment.reply_to_user_id)
        .where(ForumComment.status != "removed")
    )


def _to_out(row: Row) -> CommentOut:
    comment, nickname, mentioned = row
    # 신고로 접힌 댓글은 내용과 작성자를 보내지 않음 (D-69와 같은 방식)
    hidden = comment.status == "folded"
    return CommentOut(
        id=comment.id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        body=None if hidden else comment.body,
        author_nickname=None if hidden else nickname,
        status=comment.status,
        reply_to_nickname=mentioned,
        created_at=comment.created_at,
    )


def _comment_gone(db: Session, comment_id: int):
    if db.scalar(select(ForumComment.id).where(ForumComment.id == comment_id)) is not None:
        return api_error(404, "COMMENT_NOT_FOUND", "삭제된 댓글입니다")
    return api_error(404, "COMMENT_NOT_FOUND", "없는 댓글이에요")
