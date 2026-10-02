from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    provider: Mapped[str] = mapped_column(String(20))
    provider_user_id: Mapped[str] = mapped_column(String(255))
    # 구글에서 막 돌아온 사람은 아직 닉네임이 없음 → 비워둘 수 있게 (D-48)
    # 중복 금지는 그대로 (D-84) / 2~12자 검사는 서버 입력 검사에서
    nickname: Mapped[str | None] = mapped_column(String(20), unique=True)
    # 닉네임을 마지막으로 바꾼 시각 → 2주에 한 번만 바꿀 수 있게 (D-85)
    nickname_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
