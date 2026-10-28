"""내 정보·닉네임 (docs 07 인증, F-06)"""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Response
from sqlalchemy.exc import IntegrityError

from app.deps import CurrentUser, DbSession
from app.errors import api_error
from app.models import User
from app.schemas.user import MeOut, NicknameUpdate
from app.security import COOKIE_NAME
from app.services import users as user_service

router = APIRouter(prefix="/api/me", tags=["me"])

# 닉네임을 바꾼 뒤 다음에 바꿀 수 있을 때까지 (D-85)
COOLDOWN = timedelta(days=14)


@router.get("")
def get_me(user: CurrentUser) -> MeOut:
    """로그인한 내 정보 (닉네임이 null이면 아직 안 정한 상태)"""
    return _to_out(user)


@router.put("/nickname")
def set_nickname(data: NicknameUpdate, db: DbSession, user: CurrentUser) -> MeOut:
    """닉네임 정하기·바꾸기 (2~12자·중복 금지 D-84, 2주에 한 번 D-85)"""
    if data.nickname == user.nickname:
        return _to_out(user)

    editable_at = _editable_at(user)
    if editable_at is not None:
        days = max((editable_at - datetime.now(UTC)).days + 1, 1)
        raise api_error(
            429,
            "NICKNAME_COOLDOWN",
            f"닉네임은 2주에 한 번만 바꿀 수 있어요. {days}일 뒤에 다시 해 주세요",
        )

    user.nickname = data.nickname
    user.nickname_changed_at = datetime.now(UTC)
    try:
        db.commit()
    except IntegrityError:
        # DB의 UNIQUE 규칙에 걸림 = 같은 닉네임을 쓰는 사람이 이미 있음
        db.rollback()
        raise api_error(409, "NICKNAME_TAKEN", "이미 쓰고 있는 닉네임이에요") from None
    return _to_out(user)


def _editable_at(user: User) -> datetime | None:
    """아직 못 바꾸면 '바꿀 수 있게 되는 시각', 지금 바꿀 수 있으면 None

    처음 정하는 것(닉네임이 비어 있음)은 제한 없음
    """
    if user.nickname is None or user.nickname_changed_at is None:
        return None
    editable_at = user.nickname_changed_at + COOLDOWN
    return editable_at if editable_at > datetime.now(UTC) else None


def _to_out(user: User) -> MeOut:
    return MeOut(id=user.id, nickname=user.nickname, nickname_editable_at=_editable_at(user))


@router.delete("")
def delete_me(response: Response, db: DbSession, user: CurrentUser) -> dict[str, str]:
    """계정 삭제 (6-4)

    쓴 문장은 남고 작성자 표시만 "탈퇴한 작가"가 됨 — 뒤에 이어진 이야기가 무너지지 않도록
    """
    user_service.withdraw(db, user)
    # 로그인 표도 바로 거둠 (서버는 이미 탈퇴자로 보지만 브라우저에 남겨 둘 이유가 없음)
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "deleted"}
