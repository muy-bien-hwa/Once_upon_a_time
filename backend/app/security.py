"""로그인 표(JWT 쿠키) 만들기·읽기 (3단계 F-06)

쿠키에는 "이 사람은 우리 DB의 몇 번 유저"라는 사실만 담고, 서버 비밀값으로 서명함
→ 내용을 고치면 서명이 깨져서 바로 들통남
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

COOKIE_NAME = "session"
# 로그인 유지 기간
COOKIE_DAYS = 30

# 구글로 갔다 오는 동안만 쓰는 쿠키 (Authlib이 state를 담아 둠)
# ⚠️ 로그인 쿠키와 이름이 같으면 안 됨 — 돌아오는 응답에서 같은 이름으로 덮어써 로그인 표가 지워짐
OAUTH_COOKIE_NAME = "oauth"
# 로그인 화면에 머무는 시간만 버티면 됨 (기본값 14일은 쓸데없이 길다)
OAUTH_SECONDS = 600
_ALGORITHM = "HS256"


def create_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(days=COOKIE_DAYS)}
    return jwt.encode(payload, settings.jwt_secret.get_secret_value(), algorithm=_ALGORITHM)


def read_token(token: str) -> int | None:
    """표가 올바르면 유저 id, 아니면 None (위조·만료·형식 오류 모두 None)"""
    try:
        payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
