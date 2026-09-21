"""의존성: 요청마다 FastAPI가 먼저 실행해서 결과를 API 함수에 넘겨주는 함수들"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.errors import api_error
from app.models import User


def get_db() -> Iterator[Session]:
    """요청마다 DB 세션을 열고, 응답이 끝나면 닫음"""
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    """로그인한 유저

    2단계: .env의 DEV_USER_ID 유저를 돌려줌 (가짜 로그인)
    3단계: 이 함수 안을 JWT 쿠키 검사로 바꾸고 DEV_USER_ID 분기는 삭제
    """
    if settings.dev_user_id is None:
        raise api_error(401, "AUTH_REQUIRED", "로그인이 필요해요")
    user = db.get(User, settings.dev_user_id)
    if user is None:
        raise api_error(401, "AUTH_REQUIRED", "로그인이 필요해요")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
