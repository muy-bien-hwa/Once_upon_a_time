"""계정 삭제 (6-4)

- 누구였는지 알 수 없게 지우되, 쓴 문장은 남김 (뒤에 이어진 이야기가 무너지지 않도록)
- 같은 구글 계정으로 다시 와도 새 계정
"""

import pytest

from app.models import User
from app.services.users import WITHDRAWN, get_or_create_google_user


@pytest.fixture
def story(client):
    """내가 시작한 스토리 (탈퇴 뒤에도 남아야 함)"""
    return client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()


def test_withdrawing_clears_who_i_was(client, db_session, seed):
    before = db_session.get(User, seed["author"])
    before.email = "me@example.com"
    db_session.commit()

    assert client.delete("/api/me").json() == {"status": "deleted"}

    db_session.expire(before)
    assert before.nickname is None
    assert before.email is None
    assert before.deleted_at is not None
    assert not before.provider_user_id.startswith("author-sub")


def test_my_sentences_stay_as_a_withdrawn_author(client, story):
    root = story["sentence"]["id"]

    client.delete("/api/me")

    shown = client.get(f"/api/sentences/{root}/path").json()["items"][0]
    assert shown["content"] == "첫 문장이다."
    assert shown["author_nickname"] == WITHDRAWN


def test_the_story_is_still_listed(client, story):
    """내 첫 문장으로 시작한 스토리도 그대로 (남이 이어 쓸 수 있어야 함)"""
    client.delete("/api/me")

    card = client.get(f"/api/stories/{story['story']['id']}").json()
    assert card["first_sentence"] == "첫 문장이다."
    assert card["creator_nickname"] == WITHDRAWN


def test_the_old_cookie_stops_working(client):
    """탈퇴 뒤에는 남아 있던 로그인 표로 아무것도 못 함"""
    client.delete("/api/me")

    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)

    assert client.get("/api/me").status_code == 401


def test_the_nickname_is_released(client, db_session, seed):
    """비운 닉네임은 다른 사람이 쓸 수 있어야 함 (중복 금지 D-84와 충돌하지 않게)"""
    client.delete("/api/me")

    other = db_session.get(User, seed["voter"])
    other.nickname = "author"
    db_session.commit()

    assert other.nickname == "author"


def test_coming_back_with_the_same_google_account_is_a_new_person(client, db_session, seed):
    before = db_session.get(User, seed["author"])
    google_id = before.provider_user_id

    client.delete("/api/me")
    again = get_or_create_google_user(db_session, google_id, email="me@example.com")

    assert again.id != seed["author"]
    assert again.nickname is None


def test_withdrawing_needs_login(client):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert client.delete("/api/me").status_code == 401
