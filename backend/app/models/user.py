from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, IdMixin


class User(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id"),)

    provider: Mapped[str] = mapped_column(String(20))
    provider_user_id: Mapped[str] = mapped_column(String(255))
    # 구글 계정의 이메일. 공지와 출판 동의 요청에만 씀 (광고 없음) / 로그인할 때마다 갱신
    # 탈퇴하면 비움 — 화면·API 어디에도 내보내지 않음
    email: Mapped[str | None] = mapped_column(String(320))
    # 구글에서 막 돌아온 사람은 아직 닉네임이 없음 → 비워둘 수 있게 (D-48)
    # 중복 금지는 그대로 (D-84) / 2~12자 검사는 서버 입력 검사에서
    nickname: Mapped[str | None] = mapped_column(String(20), unique=True)
    # 닉네임을 마지막으로 바꾼 시각 → 2주에 한 번만 바꿀 수 있게 (D-85)
    nickname_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 탈퇴한 시각. 값이 있으면 로그인에 쓸 수 없는 빈 껍데기 (쓴 글은 "탈퇴한 작가"로 남음)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
