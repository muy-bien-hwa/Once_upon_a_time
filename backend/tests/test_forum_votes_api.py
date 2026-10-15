"""포럼 글 투표 (F-17·D-42·D-52)"""

import pytest
from sqlalchemy import text


@pytest.fixture
def other_post(client, db_conn, seed):
    """다른 사람(voter)이 쓴 글 → 로그인 유저(author)가 투표할 수 있음"""
    story = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    post = client.post(
        f"/api/stories/{story['story']['id']}/forum/posts",
        json={"title": "남의 글", "body": "남이 쓴 본문이다."},
    ).json()
    db_conn.execute(
        text("UPDATE forum_posts SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": post["id"]},
    )
    return post


def vote(client, post_id: int, value: int):
    return client.put(f"/api/forum/posts/{post_id}/vote", json={"value": value})


def test_vote_counts_and_shows_my_choice(client, other_post):
    body = vote(client, other_post["id"], 1).json()

    assert (body["up_count"], body["down_count"], body["my_vote"]) == (1, 0, 1)


def test_pressing_the_other_button_switches_the_vote(client, other_post):
    vote(client, other_post["id"], 1)

    body = vote(client, other_post["id"], -1).json()

    assert (body["up_count"], body["down_count"], body["my_vote"]) == (0, 1, -1)


def test_vote_can_be_cancelled(client, other_post):
    vote(client, other_post["id"], 1)

    body = client.delete(f"/api/forum/posts/{other_post['id']}/vote").json()

    assert (body["up_count"], body["my_vote"]) == (0, None)


def test_cannot_vote_on_my_own_post(client, other_post, db_conn, seed):
    db_conn.execute(
        text("UPDATE forum_posts SET author_id = :me WHERE id = :id"),
        {"me": seed["author"], "id": other_post["id"]},
    )

    response = vote(client, other_post["id"], 1)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SELF_VOTE"


def test_cannot_vote_on_a_deleted_post(client, db_conn, other_post, seed):
    db_conn.execute(
        text("UPDATE forum_posts SET status = 'removed' WHERE id = :id"), {"id": other_post["id"]}
    )

    response = vote(client, other_post["id"], 1)

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "삭제된 글입니다"


def test_my_vote_shows_up_in_the_list(client, other_post):
    vote(client, other_post["id"], -1)

    items = client.get(f"/api/stories/{other_post['story_id']}/forum/posts").json()["items"]

    assert [(item["id"], item["my_vote"]) for item in items] == [(other_post["id"], -1)]


def test_vote_needs_login(client, other_post, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.clear()

    assert vote(client, other_post["id"], 1).status_code == 401
