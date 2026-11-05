"""구글 로그인 (docs 07 인증, F-06)

구글 서버를 실제로 부르지 않고, "구글이 이렇게 답했다"고 가짜로 채워서 흐름만 검사
"""

import base64
import json

import itsdangerous
import pytest
from sqlalchemy import text

from app.config import settings
from app.security import (
    COOKIE_NAME,
    OAUTH_COOKIE_NAME,
    create_token,
    read_token,
)

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


def test_login_cookie_is_used_for_writing(client, db_session, seed):
    """쿠키만으로 로그인한 상태가 되는지 (가짜 로그인 DEV_USER_ID 없이)"""
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.set(COOKIE_NAME, create_token(seed["author"]))

    response = client.post(
        "/api/stories", json={"title": "쿠키로 쓴 글", "content": "첫 문장이다."}
    )

    assert response.status_code == 201
    assert response.json()["sentence"]["author_nickname"] == "author"


def test_login_cookie_is_not_wiped_on_the_way_back(client, monkeypatch):
    """구글에서 돌아올 때 로그인 표가 살아남아야 함

    Authlib은 돌아오는 길에 state를 세션에서 꺼내며 세션을 비운다. 그 세션 쿠키 이름이
    로그인 쿠키와 같으면, 같은 응답에 "지우기" 줄이 한 번 더 붙어 로그인 표가 사라진다.
    오류가 아니라 정상 응답이라 아무 문구도 안 뜬 채 로그아웃 상태가 된다 (2026-11-05 운영에서 겪음).
    """
    from app.routers import auth

    async def fake_token(request):
        request.session.pop("_state_google_abc", None)  # Authlib이 하는 일
        return {"userinfo": {"sub": GOOGLE_SUB, "email": "reader@example.com"}}

    monkeypatch.setattr(auth.oauth.google, "authorize_access_token", fake_token)
    # 구글로 갈 때 심어 둔 왕복용 쿠키를 손으로 만들어 들려 보냄
    signer = itsdangerous.TimestampSigner(settings.jwt_secret.get_secret_value() or "dev-only")
    state = base64.b64encode(json.dumps({"_state_google_abc": {"data": {}}}).encode())
    client.cookies.set(OAUTH_COOKIE_NAME, signer.sign(state).decode())

    response = client.get("/auth/google/callback", follow_redirects=False)

    sent = [
        line
        for line in response.headers.get_list("set-cookie")
        if line.startswith(f"{COOKIE_NAME}=")
    ]
    # 로그인 쿠키를 건드리는 줄은 딱 하나여야 한다 (두 줄이면 뒤엣것이 앞엣것을 지운다)
    assert len(sent) == 1
    assert read_token(sent[0].split("=", 1)[1].split(";")[0]) is not None


def test_logout_clears_the_cookie(client):
    client.cookies.set(COOKIE_NAME, create_token(1))

    response = client.post("/auth/logout")

    assert response.status_code == 200
    assert response.cookies.get(COOKIE_NAME) is None
