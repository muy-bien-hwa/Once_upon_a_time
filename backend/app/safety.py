"""배포 전 자기 점검 + 브라우저에 보내는 안전 규칙 (6-3 보안 점검)

- 운영(https)으로 뜰 때 설정이 빠졌으면 **서버를 아예 띄우지 않음** → 조용히 위험하게 도는 것보다 낫다
- 응답마다 브라우저에게 지켜야 할 규칙(헤더)을 함께 보냄
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# 로그인 표를 서명하는 비밀값은 이 길이 이상 (짧으면 찍어 맞힐 수 있음)
MIN_SECRET = 32

# 한 번에 받는 내용의 최대 크기 (가장 긴 글이 5,000자라 1MB면 넉넉함)
# 없으면 누가 거대한 요청 하나로 서버 메모리를 가득 채울 수 있음
MAX_BODY = 1_000_000

# 브라우저에게 주는 규칙 — 화면이 쓰는 곳만 허용 (글꼴 CDN·구글 폰트)
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
    "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


def check_settings() -> None:
    """운영 설정이 갖춰졌는지 확인. 모자라면 뜨지 않고 무엇이 빠졌는지 알려 줌"""
    secret = settings.jwt_secret.get_secret_value()
    production = settings.cookie_secure  # https로 서비스한다 = 운영

    missing = []
    if len(secret) < MIN_SECRET:
        missing.append(f"JWT_SECRET (로그인 표 서명용, {MIN_SECRET}자 이상 무작위 문자열)")
    if not settings.google_client_id or not settings.google_client_secret.get_secret_value():
        missing.append("GOOGLE_CLIENT_ID · GOOGLE_CLIENT_SECRET")
    if settings.db_url is None and not settings.db_password.get_secret_value():
        missing.append("DATABASE_URL (또는 DB_PASSWORD)")
    if production and not settings.backend_origin.startswith("https://"):
        missing.append("BACKEND_ORIGIN (배포 주소를 https로)")

    if not missing:
        return
    if production:
        raise RuntimeError("운영 설정이 빠졌습니다 — " + " / ".join(missing))
    logger.warning("개발 중이라 넘어감 (배포 전에 채워야 함): %s", " / ".join(missing))


class SafetyHeaders(BaseHTTPMiddleware):
    """너무 큰 요청은 돌려보내고, 응답마다 브라우저 안전 규칙을 붙임"""

    async def dispatch(self, request: Request, call_next):
        length = request.headers.get("content-length")
        if length is not None and length.isdigit() and int(length) > MAX_BODY:
            return JSONResponse(
                status_code=413,
                content={"detail": {"code": "TOO_LARGE", "message": "보낸 내용이 너무 커요"}},
            )

        response = await call_next(request)
        headers = response.headers
        # 파일 종류를 멋대로 추측하지 않기 / 다른 사이트가 우리 화면을 액자처럼 끼우지 못하게
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # 카메라·마이크·위치는 쓰지 않으므로 아예 막아 둠
        headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # API 문서 화면은 스크립트를 CDN에서 받아 오므로 그 화면만 빼고 적용
        if not request.url.path.startswith("/api/docs"):
            headers.setdefault("Content-Security-Policy", CSP)
        if settings.cookie_secure:
            headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def guard(app: FastAPI) -> None:
    check_settings()
    app.add_middleware(SafetyHeaders)
