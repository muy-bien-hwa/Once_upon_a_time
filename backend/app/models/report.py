from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin


class Report(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        # 문장·글·댓글 중 정확히 하나만 채움
        CheckConstraint("num_nonnulls(sentence_id, post_id, comment_id) = 1", name="one_target"),
        # 같은 대상 중복 신고 금지 (대상 id를 앞에 둬서 대상별 신고 수 세기에도 쓰임)
        UniqueConstraint("sentence_id", "reporter_id"),
        UniqueConstraint("post_id", "reporter_id"),
        UniqueConstraint("comment_id", "reporter_id"),
    )

    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    sentence_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("sentences.id"))
    post_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("forum_posts.id"))
    comment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("forum_comments.id"))
