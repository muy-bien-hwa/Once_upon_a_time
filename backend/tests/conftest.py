import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

# 테스트는 개발 DB(relay)가 아니라 테스트 DB(relay_test)를 씀
# app 코드가 설정을 읽기 전에 정해야 해서 파일 맨 위에서 설정
os.environ["DB_NAME"] = "relay_test"

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    """테스트를 시작하기 전에 relay_test에 최신 마이그레이션을 적용"""
    command.upgrade(Config(str(ALEMBIC_INI)), "head")


@pytest.fixture
def db_conn():
    """테스트마다 트랜잭션을 열고 끝나면 되돌림 → 테스트 데이터가 DB에 남지 않음"""
    from app.db import engine

    with engine.connect() as conn:
        trans = conn.begin()
        yield conn
        trans.rollback()


@pytest.fixture
def db_session(db_conn):
    """API 테스트용 세션: 테스트 트랜잭션 안에서 동작 → 코드가 저장(commit)해도 끝나면 전부 되돌림"""
    from sqlalchemy.orm import Session

    session = Session(
        bind=db_conn, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    yield session
    session.close()


@pytest.fixture
def client(db_session, seed):
    """API 호출용 클라이언트: 테스트 DB 세션을 쓰고, 로그인 유저는 seed의 작가"""
    from fastapi.testclient import TestClient

    from app.deps import get_current_user, get_db
    from app.main import app
    from app.models import User

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: db_session.get(User, seed["author"])
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed(db_conn):
    """테스트용 기본 데이터: 작가 1명, 투표자 1명, 스토리 1개"""
    add_user = text(
        "INSERT INTO users (provider, provider_user_id, nickname) "
        "VALUES ('google', :sub, :nickname) RETURNING id"
    )
    author_id = db_conn.execute(add_user, {"sub": "author-sub", "nickname": "author"}).scalar_one()
    voter_id = db_conn.execute(add_user, {"sub": "voter-sub", "nickname": "voter"}).scalar_one()
    story_id = db_conn.execute(
        text("INSERT INTO stories (title, creator_id) VALUES ('옛날 옛적에', :u) RETURNING id"),
        {"u": author_id},
    ).scalar_one()
    return {"author": author_id, "voter": voter_id, "story": story_id}
