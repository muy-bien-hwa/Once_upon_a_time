from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import STATUS_CHECK, Base, CreatedAtMixin, IdMixin


class ForumPost(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "forum_posts"
    __table_args__ = (
        CheckConstraint("pin_slot IN (1, 2)", name="pin_slot_valid"),
        CheckConstraint(STATUS_CHECK, name="status_valid"),
        # NULL끼리는 중복으로 보지 않음 → 일반 글은 개수 제한 없음, 고정글만 스토리당 2개
        UniqueConstraint("story_id", "pin_slot"),
        Index("ix_forum_posts_story_id_created_at", "story_id", "created_at"),
    )

    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stories.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(100))
    body: Mapped[str] = mapped_column(String(5000))
    quoted_sentence_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sentences.id")
    )
    pin_slot: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(10), server_default="active")


class ForumPostVote(CreatedAtMixin, Base):
    __tablename__ = "forum_post_votes"
    __table_args__ = (
        CheckConstraint("value IN (1, -1)", name="value_valid"),
        Index("ix_forum_post_votes_post_id", "post_id"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("forum_posts.id"), primary_key=True
    )
    value: Mapped[int] = mapped_column(SmallInteger)


class ForumComment(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "forum_comments"
    __table_args__ = (
        CheckConstraint(STATUS_CHECK, name="status_valid"),
        Index("ix_forum_comments_post_id_created_at", "post_id", "created_at"),
    )

    post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("forum_posts.id"))
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("forum_comments.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(10), server_default="active")
