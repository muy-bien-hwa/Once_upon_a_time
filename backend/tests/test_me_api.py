"""내 정보·닉네임 (docs 07 인증, D-84)"""

import pytest
from sqlalchemy import text

from app.security import COOKIE_NAME, create_token

NEW_USER = text(
    "INSERT INTO users (provider, provider_user_id) VALUES ('google', :sub) RETURNING id"
)


@pytest.fixture
def fresh_login(client, db_conn, monkeypatch):
    """닉네임을 아직 안 정한 사람으로 로그인한 상태"""
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    # 가짜 로그인이 끼어들지 않게 (테스트가 끝나면 monkeypatch가 되돌림)
    monkeypatch.setattr(settings, "dev_user_id", None)
    user_id = db_conn.execute(NEW_USER, {"sub": "brand-new"}).scalar_one()
    client.cookies.set(COOKIE_NAME, create_token(user_id))
    return user_id


def test_me_needs_login(client):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


def test_new_user_has_no_nickname_yet(client, fresh_login):
    body = client.get("/api/me").json()

    assert body["id"] == fresh_login
    assert body["nickname"] is None


def test_writing_before_choosing_a_nickname_is_blocked(client, fresh_login):
    response = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."})

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NICKNAME_REQUIRED"


def test_setting_a_nickname_lets_you_write(client, fresh_login):
    set_response = client.put("/api/me/nickname", json={"nickname": "  새작가  "})

    # 앞뒤 공백은 자동으로 지움
    assert set_response.json()["nickname"] == "새작가"

    created = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."})

    assert created.status_code == 201
    assert created.json()["sentence"]["author_nickname"] == "새작가"


@pytest.mark.parametrize(
    "nickname",
    ["한", " ", "가" * 13, "줄\n바꿈"],
    ids=["too-short", "blank", "too-long", "newline"],
)
def test_bad_nicknames_are_rejected(client, fresh_login, nickname):
    assert client.put("/api/me/nickname", json={"nickname": nickname}).status_code == 422


def test_duplicate_nickname_is_rejected(client, fresh_login, seed):
    # seed의 작가가 이미 "author"를 쓰고 있음
    response = client.put("/api/me/nickname", json={"nickname": "author"})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "NICKNAME_TAKEN"
    # 실패 후에도 다른 닉네임으로는 정할 수 있어야 함
    assert client.put("/api/me/nickname", json={"nickname": "다른작가"}).status_code == 200


def set_changed_at(db_conn, user_id: int, days_ago: int) -> None:
    db_conn.execute(
        text(
            "UPDATE users SET nickname_changed_at = now() - make_interval(days => :days) "
            "WHERE id = :id"
        ),
        {"days": days_ago, "id": user_id},
    )


def test_nickname_cannot_be_changed_twice_in_two_weeks(client, fresh_login):
    client.put("/api/me/nickname", json={"nickname": "처음이름"})

    response = client.put("/api/me/nickname", json={"nickname": "바꾼이름"})

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "NICKNAME_COOLDOWN"
    assert client.get("/api/me").json()["nickname"] == "처음이름"


def test_me_tells_when_the_nickname_can_change_again(client, fresh_login):
    assert client.get("/api/me").json()["nickname_editable_at"] is None  # 처음엔 제한 없음

    client.put("/api/me/nickname", json={"nickname": "처음이름"})

    assert client.get("/api/me").json()["nickname_editable_at"] is not None


def test_nickname_can_be_changed_after_two_weeks(client, db_conn, fresh_login):
    client.put("/api/me/nickname", json={"nickname": "처음이름"})
    set_changed_at(db_conn, fresh_login, days_ago=15)

    response = client.put("/api/me/nickname", json={"nickname": "바꾼이름"})

    assert response.status_code == 200
    assert response.json()["nickname"] == "바꾼이름"


def test_resubmitting_the_same_nickname_is_fine(client, fresh_login):
    client.put("/api/me/nickname", json={"nickname": "처음이름"})

    assert client.put("/api/me/nickname", json={"nickname": "처음이름"}).status_code == 200
