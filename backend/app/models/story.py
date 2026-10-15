from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin


class Story(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "stories"
    __table_args__ = (
        CheckConstraint(r"title ~ '\S'", name="title_not_blank"),
        Index("ix_stories_creator_id_created_at", "creator_id", "created_at"),
        Index("ix_stories_created_at", "created_at"),
    )

    title: Mapped[str] = mapped_column(String(50))
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))


class StoryRecommendation(CreatedAtMixin, Base):
    __tablename__ = "story_recommendations"
    __table_args__ = (Index("ix_story_recommendations_story_id", "story_id"),)

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stories.id"), primary_key=True)


class StoryManager(CreatedAtMixin, Base):
    """스토리 관리자 (D-91)

    스토리를 시작한 작가가 임명하며, 하는 일은 커뮤니티 글 고정·해제뿐
    """

    __tablename__ = "story_managers"

    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stories.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
