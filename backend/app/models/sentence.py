from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import STATUS_CHECK, Base, CreatedAtMixin, IdMixin


# 파이썬 클래스 1개 = 테이블 1개. id·created_at은 공통 부품에서 받아옴
class Sentence(IdMixin, CreatedAtMixin, Base):
    # DB에 만들어질 테이블 이름
    __tablename__ = "sentences"
    # 테이블 전체에 거는 규칙
    __table_args__ = (
        # 공백만 있는 문장 거부
        CheckConstraint(r"content ~ '\S'", name="content_not_blank"),
        CheckConstraint("depth >= 0", name="depth_non_negative"),
        # 부모 없음 ⇔ 깊이 0
        CheckConstraint("(parent_id IS NULL) = (depth = 0)", name="root_iff_depth_zero"),
        # 첫 문장은 삭제될 수 없음 (D-66)
        CheckConstraint("parent_id IS NOT NULL OR status <> 'deleted'", name="root_not_deleted"),
        CheckConstraint(STATUS_CHECK, name="status_valid"),
        # 인덱스 만들기
        Index("ix_sentences_parent_id", "parent_id"),
        Index("ix_sentences_story_id_depth", "story_id", "depth"),
        Index("ix_sentences_author_id_story_id_created_at", "author_id", "story_id", "created_at"),
        # 스토리당 첫 문장(parent_id가 빈 문장)은 1개만 (D-65)
        Index(
            "uq_sentences_one_root_per_story",
            "story_id",
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
    )

    # 필수 + stories 테이블 참조
    story_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stories.id"))
    # `| None` = 비어도 됨 (첫 문장)
    parent_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("sentences.id"))
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    # 최대 100자
    content: Mapped[str] = mapped_column(String(100))
    depth: Mapped[int] = mapped_column(Integer)
    # 값을 안 주면 'active'
    status: Mapped[str] = mapped_column(String(10), server_default="active")


class SentenceVote(CreatedAtMixin, Base):
    __tablename__ = "sentence_votes"
    __table_args__ = (
        CheckConstraint("value IN (1, -1)", name="value_valid"),
        Index("ix_sentence_votes_sentence_id", "sentence_id"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    sentence_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sentences.id"), primary_key=True
    )
    value: Mapped[int] = mapped_column(SmallInteger)
