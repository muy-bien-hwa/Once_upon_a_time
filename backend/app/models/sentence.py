from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import STATUS_CHECK, Base, CreatedAtMixin, IdMixin


class Sentence(
    IdMixin, CreatedAtMixin, Base
):  # 파이썬 클래스 1개 = 테이블 1개. id·created_at은 공통 부품에서 받아옴
    __tablename__ = "sentences"  # DB에 만들어질 테이블 이름
    __table_args__ = (  # 테이블 전체에 거는 규칙
        CheckConstraint(
            r"content ~ '\S'", name="content_not_blank"
        ),  # PostgreSQL 정규식 비교: content에 "공백(스페이스·탭·줄바꿈)이 아닌 글자 1개라도 있는가?
        CheckConstraint("depth >= 0", name="depth_non_negative"),
        CheckConstraint(
            "(parent_id IS NULL) = (depth = 0)", name="root_iff_depth_zero"
        ),  # 부모 없음 ⇔ 깊이 0
        CheckConstraint(STATUS_CHECK, name="status_valid"),
        Index("ix_sentences_parent_id", "parent_id"),  # 인덱스 만들기
        Index("ix_sentences_story_id_depth", "story_id", "depth"),
        Index("ix_sentences_author_id_story_id_created_at", "author_id", "story_id", "created_at"),
    )

    story_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stories.id")
    )  # 필수 + stories 테이블 참조
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sentences.id")
    )  # `| None` = 비어도 됨 (첫 문장)
    author_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String(100))  # 최대 100자
    depth: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(10), server_default="active"
    )  # 값을 안 주면 'active'


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
