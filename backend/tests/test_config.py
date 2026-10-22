"""DB 접속 설정 (6-3)

개발 PC는 조각(DB_HOST·DB_USER…)으로, 운영은 한 줄짜리 DATABASE_URL로 붙음
→ DB를 옮길 때 그 한 줄만 바꾸면 되도록
"""

import pytest

from app.config import Settings

NEON = "postgresql://writer:pw@ep-cool-1.ap-southeast-1.aws.neon.tech/relay?sslmode=require"


@pytest.fixture
def clean_env(monkeypatch):
    """`.env`와 실제 환경변수를 끄고 시작 (테스트끼리 영향을 주지 않게)"""
    for name in ("DATABASE_URL", "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"):
        monkeypatch.delenv(name, raising=False)


def settings_with(**env) -> Settings:
    return Settings(_env_file=None, **env)


def test_pieces_are_used_when_there_is_no_url(clean_env):
    url = settings_with(
        DB_HOST="localhost", DB_USER="postgres", DB_PASSWORD="비밀", DB_NAME="relay"
    )
    url = url.database_url

    assert (url.drivername, url.host, url.database) == ("postgresql+psycopg", "localhost", "relay")
    assert url.password == "비밀"


def test_connection_string_wins(clean_env):
    url = settings_with(DB_HOST="localhost", DB_PASSWORD="개발용", DATABASE_URL=NEON).database_url

    assert url.host == "ep-cool-1.ap-southeast-1.aws.neon.tech"
    assert url.database == "relay"
    assert url.username == "writer"


def test_driver_is_swapped_in_for_psycopg(clean_env):
    """Neon·Render가 주는 `postgresql://`를 그대로 쓰면 psycopg2를 찾다가 실패함"""
    assert settings_with(DATABASE_URL=NEON).database_url.drivername == "postgresql+psycopg"
    assert (
        settings_with(DATABASE_URL="postgres://u:p@host/db").database_url.drivername
        == "postgresql+psycopg"
    )


def test_ssl_setting_is_kept(clean_env):
    """sslmode를 잃어버리면 Neon이 연결을 거부함"""
    assert settings_with(DATABASE_URL=NEON).database_url.query["sslmode"] == "require"


def test_password_is_not_printed(clean_env):
    """설정을 그대로 출력해도 비밀번호가 보이지 않아야 함 (로그에 새는 사고 방지)"""
    printed = repr(settings_with(DB_PASSWORD="비밀번호", DATABASE_URL=NEON))

    assert "비밀번호" not in printed
    assert "pw@" not in printed
