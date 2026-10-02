"""의존성: 요청마다 FastAPI가 먼저 실행해서 결과를 API 함수에 넘겨주는 함수들"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.errors import api_error
from app.models import User
from app.security import COOKIE_NAME, read_token


def get_db() -> Iterator[Session]:
    """요청마다 DB 세션을 열고, 응답이 끝나면 닫음"""
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, request: Request) -> User:
    """로그인한 유저 (쿠키의 로그인 표를 읽음)

    DEV_USER_ID 분기는 3-1 마지막 단계에서 삭제 (운영에 남으면 누구나 그 유저가 됨)
    """
    token = request.cookies.get(COOKIE_NAME)
    user_id = read_token(token) if token else settings.dev_user_id
    user = db.get(User, user_id) if user_id is not None else None
    if user is None:
        raise api_error(401, "AUTH_REQUIRED", "로그인이 필요해요")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_author(user: CurrentUser) -> User:
    """글을 쓰려면 닉네임까지 정한 상태여야 함 (D-48) → 닉네임이 없으면 403"""
    if user.nickname is None:
        raise api_error(403, "NICKNAME_REQUIRED", "닉네임을 먼저 정해 주세요")
    return user


CurrentAuthor = Annotated[User, Depends(get_current_author)]
