"""스토리 추천 (docs 07 추천, F-13·D-54)"""

import pytest
from sqlalchemy import text

ADD_STORY = text("INSERT INTO stories (title, creator_id) VALUES (:title, :author) RETURNING id")
ADD_ROOT = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, NULL, :author, :content, 0, 'active') RETURNING id"
)


@pytest.fixture
def other_story(client, db_conn, seed):
    """다른 사람(voter)이 만든 스토리 → 로그인 유저(author)가 추천할 수 있음"""
    story_id = db_conn.execute(
        ADD_STORY, {"title": "남이 시작한 스토리", "author": seed["voter"]}
    ).scalar_one()
    db_conn.execute(
        ADD_ROOT,
        {"story": story_id, "author": seed["voter"], "content": "다른 사람의 첫 문장이다."},
    )
    return story_id


def recommend(client, story_id: int):
    return client.put(f"/api/stories/{story_id}/recommendation")


def test_recommend_counts_and_shows_my_press(client, other_story):
    body = recommend(client, other_story).json()

    assert (body["recommend_count"], body["my_recommendation"]) == (1, True)


def test_recommending_twice_counts_once(client, other_story):
    recommend(client, other_story)

    body = recommend(client, other_story).json()

    assert body["recommend_count"] == 1


def test_recommendation_can_be_cancelled(client, other_story):
    recommend(client, other_story)

    body = client.delete(f"/api/stories/{other_story}/recommendation").json()

    assert (body["recommend_count"], body["my_recommendation"]) == (0, False)


def test_cannot_recommend_my_own_story(client):
    mine = client.post(
        "/api/stories", json={"title": "내 스토리", "content": "내 문장이다."}
    ).json()

    response = recommend(client, mine["story"]["id"])

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SELF_RECOMMEND"


def test_cannot_recommend_a_story_whose_first_sentence_is_folded(client, db_conn, other_story):
    db_conn.execute(
        text("UPDATE sentences SET status = 'folded' WHERE story_id = :id"), {"id": other_story}
    )

    response = recommend(client, other_story)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "RECOMMEND_NOT_ALLOWED"


def test_recommending_a_missing_story_is_404(client):
    response = recommend(client, 10_000_000)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "STORY_NOT_FOUND"


def test_recommendation_needs_login(client, other_story, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.clear()

    assert recommend(client, other_story).status_code == 401


def test_my_recommendation_shows_up_in_the_list(client, other_story):
    recommend(client, other_story)

    items = client.get("/api/stories").json()["items"]

    pressed = [item["id"] for item in items if item["my_recommendation"]]
    assert pressed == [other_story]


def test_recommended_sort_puts_the_recommended_story_first(client, other_story):
    client.post("/api/stories", json={"title": "내 스토리", "content": "내 문장이다."})
    recommend(client, other_story)

    items = client.get("/api/stories?sort=recommended").json()["items"]

    assert items[0]["id"] == other_story
