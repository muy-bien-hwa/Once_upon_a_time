"""내 정보 API가 주고받는 데이터 모양 (docs 07 인증)"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, StringConstraints

# 닉네임: 앞뒤 공백을 지운 뒤 2~12자, 줄바꿈 금지 (D-84)
Nickname = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=12, pattern=r"^[^\r\n]*$"),
]


class MeOut(BaseModel):
    id: int
    # 첫 로그인 직후에는 아직 없음 → 화면에서 닉네임 정하기로 보냄 (D-48)
    nickname: str | None
    # 다음에 닉네임을 바꿀 수 있는 시각 / null이면 지금 바꿀 수 있음 (D-85)
    nickname_editable_at: datetime | None


class NicknameUpdate(BaseModel):
    nickname: Nickname
