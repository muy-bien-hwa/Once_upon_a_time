import logging

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine
from app.routers import sentences, stories

logger = logging.getLogger(__name__)

# API 문서 화면도 /api 아래에 둠 (D-35 경로 규칙, 개발 프록시로도 열림)
app = FastAPI(
    title="Once upon a time API",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)
app.include_router(stories.router)
app.include_router(sentences.router)


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
