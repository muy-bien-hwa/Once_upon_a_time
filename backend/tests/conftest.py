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
