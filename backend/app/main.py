import logging

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

from app import safety, web
from app.config import settings
from app.db import engine
from app.routers import auth, forum, me, sentences, stats, stories, users
from app.security import OAUTH_COOKIE_NAME, OAUTH_SECONDS

logger = logging.getLogger(__name__)

# API 문서 화면도 /api 아래에 둠 (D-35 경로 규칙, 개발 프록시로도 열림)
# 배포에서는 닫음 → 주소는 safety.docs_url()이 정함
app = FastAPI(
    title="Once upon a time API",
    docs_url=safety.docs_url(),
    openapi_url=None if safety.docs_url() is None else "/api/openapi.json",
    redoc_url=None,
)

# 설정이 모자란 채로 배포되지 않게 먼저 확인 + 응답 안전 규칙(헤더) 붙이기
safety.guard(app)

# 구글 로그인 중간 단계(state)를 잠깐 보관하는 쿠키 (Authlib이 사용)
# 이름을 로그인 쿠키와 다르게 둬야 함 — 같으면 돌아오는 길에 로그인 표가 지워진다 (security.py)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret.get_secret_value() or "dev-only",
    session_cookie=OAUTH_COOKIE_NAME,
    max_age=OAUTH_SECONDS,
    https_only=settings.cookie_secure,
    same_site="lax",
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(stories.router)
app.include_router(sentences.router)
app.include_router(stats.router)
app.include_router(forum.router)
app.include_router(users.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db = "ok"
    except SQLAlchemyError:
        logger.exception("DB connection failed")
        db = "error"
    return {"status": "ok", "db": db}


# 화면 내보내기는 맨 마지막 (API 주소가 먼저 잡히도록)
web.mount(app)
