from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin

# 신고 사유 7종 (D-93) — 화면 토글과 같은 순서
REASONS = (
    "abuse",  # 욕설·비방
    "sexual",  # 음란·선정성
    "violence",  # 폭력·잔혹
    "spam",  # 광고·도배
    "privacy",  # 개인정보 노출
    "plagiarism",  # 표절
    "other",  # 기타 (설명 필수)
)
REASON_CHECK = "reason IN (" + ", ".join(f"'{reason}'" for reason in REASONS) + ")"


class Report(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        # 문장·글·댓글 중 정확히 하나만 채움
        CheckConstraint("num_nonnulls(sentence_id, post_id, comment_id) = 1", name="one_target"),
        CheckConstraint(REASON_CHECK, name="reason_valid"),
        # 같은 대상 중복 신고 금지 (대상 id를 앞에 둬서 대상별 신고 수 세기에도 쓰임)
        UniqueConstraint("sentence_id", "reporter_id"),
        UniqueConstraint("post_id", "reporter_id"),
        UniqueConstraint("comment_id", "reporter_id"),
    )

    reporter_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    sentence_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("sentences.id"))
    post_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("forum_posts.id"))
    comment_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("forum_comments.id"))
    # 신고 사유 1개 + 설명 500자 (기타는 설명 필수) / 신고 내용은 PM만 봄 (D-93)
    reason: Mapped[str] = mapped_column(String(20))
    detail: Mapped[str] = mapped_column(String(500), server_default="")
