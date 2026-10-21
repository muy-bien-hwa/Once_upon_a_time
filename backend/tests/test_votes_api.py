"""문장 투표 (docs 07 투표, F-07·D-52·D-82)"""

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, :parent, :author, :content, :depth, :status) RETURNING id"
)


@pytest.fixture
def other_sentence(client, db_conn, seed):
    """다른 사람(voter)이 쓴 문장 → 로그인 유저(author)가 투표할 수 있음"""
    story = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    return db_conn.execute(
        ADD_SENTENCE,
        {
            "story": story["story"]["id"],
            "parent": story["sentence"]["id"],
            "author": seed["voter"],
            "content": "다른 사람이 쓴 문장이다.",
            "depth": 1,
            "status": "active",
        },
    ).scalar_one()


def vote(client, sentence_id: int, value: int):
    return client.put(f"/api/sentences/{sentence_id}/vote", json={"value": value})


def test_vote_counts_and_shows_my_choice(client, other_sentence):
    body = vote(client, other_sentence, 1).json()

    assert (body["up_count"], body["down_count"], body["my_vote"]) == (1, 0, 1)


def test_pressing_the_other_button_switches_the_vote(client, other_sentence):
    vote(client, other_sentence, 1)

    body = vote(client, other_sentence, -1).json()

    # 추천을 따로 취소하지 않아도 비추천으로 바뀜
    assert (body["up_count"], body["down_count"], body["my_vote"]) == (0, 1, -1)


def test_vote_can_be_cancelled(client, other_sentence):
    vote(client, other_sentence, 1)

    body = client.delete(f"/api/sentences/{other_sentence}/vote").json()

    assert (body["up_count"], body["my_vote"]) == (0, None)


def test_voting_twice_counts_once(client, other_sentence):
    vote(client, other_sentence, 1)

    body = vote(client, other_sentence, 1).json()

    assert body["up_count"] == 1


def test_cannot_vote_on_my_own_sentence(client):
    mine = client.post("/api/stories", json={"title": "제목", "content": "내 문장이다."}).json()

    response = vote(client, mine["sentence"]["id"], 1)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SELF_VOTE"


@pytest.mark.parametrize("status", ["folded", "deleted"], ids=["folded", "deleted"])
def test_cannot_vote_on_hidden_content(client, db_conn, other_sentence, status):
    db_conn.execute(
        text("UPDATE sentences SET status = :status WHERE id = :id"),
        {"status": status, "id": other_sentence},
    )

    response = vote(client, other_sentence, 1)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "VOTE_NOT_ALLOWED"


def test_cannot_vote_inside_a_hidden_story(client, db_conn, other_sentence):
    """첫 문장을 숨기면 스토리 전체가 사라진 셈 → 그 안의 문장에도 투표할 수 없어야 함"""
    story_id = db_conn.execute(
        text("SELECT story_id FROM sentences WHERE id = :id"), {"id": other_sentence}
    ).scalar_one()
    db_conn.execute(
        text("UPDATE sentences SET status = 'removed' WHERE story_id = :id AND parent_id IS NULL"),
        {"id": story_id},
    )

    response = vote(client, other_sentence, 1)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "SENTENCE_NOT_FOUND"


def test_vote_needs_login(client, other_sentence):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert vote(client, other_sentence, 1).status_code == 401


def test_my_vote_shows_up_in_the_children_list(client, db_conn, other_sentence, seed):
    vote(client, other_sentence, -1)
    parent = db_conn.execute(
        text("SELECT parent_id FROM sentences WHERE id = :id"), {"id": other_sentence}
    ).scalar_one()

    items = client.get(f"/api/sentences/{parent}/children").json()["items"]

    assert [item["my_vote"] for item in items] == [-1]
