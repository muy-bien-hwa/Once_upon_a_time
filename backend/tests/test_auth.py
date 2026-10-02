"""구글 로그인 (docs 07 인증, F-06)

구글 서버를 실제로 부르지 않고, "구글이 이렇게 답했다"고 가짜로 채워서 흐름만 검사
"""

import pytest
from sqlalchemy import text

from app.security import COOKIE_NAME, create_token, read_token

GOOGLE_SUB = "google-sub-123"


@pytest.fixture
def fake_google(monkeypatch):
    """구글 응답을 가짜로 바꾸기"""
    from app.routers import auth

    async def fake_token(request):
        return {"userinfo": {"sub": GOOGLE_SUB, "email": "reader@example.com"}}

    monkeypatch.setattr(auth.oauth.google, "authorize_access_token", fake_token)


def test_token_round_trip():
    assert read_token(create_token(7)) == 7


@pytest.mark.parametrize(
    "token",
    ["", "not-a-token", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3In0.wrong-signature"],
    ids=["empty", "garbage", "fake-signature"],
)
def test_bad_token_is_rejected(token):
    assert read_token(token) is None


def test_callback_creates_user_and_sets_cookie(client, db_session, fake_google):
    response = client.get("/auth/google/callback", follow_redirects=False)

    assert response.status_code == 307
    assert COOKIE_NAME in response.cookies
    user_id = read_token(response.cookies[COOKIE_NAME])
    nickname = db_session.execute(
        text("SELECT nickname FROM users WHERE id = :id"), {"id": user_id}
    ).scalar_one()
    # 첫 로그인이라 닉네임은 아직 비어 있음 (D-48·D-84)
    assert nickname is None


def test_callback_reuses_the_same_user(client, fake_google):
    first = client.get("/auth/google/callback", follow_redirects=False)
    second = client.get("/auth/google/callback", follow_redirects=False)

    assert read_token(first.cookies[COOKIE_NAME]) == read_token(second.cookies[COOKIE_NAME])


def test_login_cookie_is_used_for_writing(client, db_session, seed, monkeypatch):
    """쿠키만으로 로그인한 상태가 되는지 (가짜 로그인 DEV_USER_ID 없이)"""
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.set(COOKIE_NAME, create_token(seed["author"]))

    response = client.post(
        "/api/stories", json={"title": "쿠키로 쓴 글", "content": "첫 문장이다."}
    )

    assert response.status_code == 201
    assert response.json()["sentence"]["author_nickname"] == "author"


def test_logout_clears_the_cookie(client):
    client.cookies.set(COOKIE_NAME, create_token(1))

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.cookies.get(COOKIE_NAME) is None
