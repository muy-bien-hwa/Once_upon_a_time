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


@pytest.mark.parametrize(
    "pasted",
    [
        f"'{NEON}'",  # 따옴표로 감싸 붙여넣음
        f'"{NEON}"',
        f"psql '{NEON}'",  # Neon 콘솔의 psql 명령을 통째로
        f"  {NEON}  ",  # 앞뒤 공백
        NEON.replace("@", "@" + chr(10)),  # 줄이 접혀 줄바꿈이 낌
    ],
    ids=["작은따옴표", "큰따옴표", "psql명령", "공백", "줄바꿈"],
)
def test_pasting_mistakes_are_cleaned_up(clean_env, pasted):
    """배포 설정칸에 붙여넣다 흔히 섞이는 것들 — 알아서 털어 내고 붙음"""
    url = settings_with(DATABASE_URL=pasted).database_url

    assert url.host == "ep-cool-1.ap-southeast-1.aws.neon.tech"
    assert url.query["sslmode"] == "require"


def test_empty_value_is_treated_as_unset(clean_env):
    """설정칸만 만들고 값을 안 넣은 경우 → 조각 설정으로 돌아감"""
    url = settings_with(DATABASE_URL="  ", DB_HOST="localhost", DB_PASSWORD="x").database_url

    assert url.host == "localhost"


def test_unreadable_value_says_what_to_fix(clean_env):
    """고칠 방법을 알려 주되, 비밀번호가 들어 있는 값 자체는 절대 출력하지 않음"""
    broken = settings_with(DATABASE_URL="여기에_주소를_넣으세요:비밀번호123")

    with pytest.raises(RuntimeError, match="DATABASE_URL") as problem:
        _ = broken.database_url

    assert "비밀번호123" not in str(problem.value)
