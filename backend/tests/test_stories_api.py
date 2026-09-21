"""스토리 API (docs 07 #1~#3)"""

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, :parent, :author, :content, :depth, :status) RETURNING id"
)


def create_story(client, title="옛날 옛적에", content="고양이가 살았다."):
    response = client.post("/api/stories", json={"title": title, "content": content})
    assert response.status_code == 201, response.text
    return response.json()


def add_sentence(db_conn, seed, story, content, parent=None, depth=0, status="active"):
    params = {
        "story": story,
        "parent": parent,
        "author": seed["author"],
        "content": content,
        "depth": depth,
        "status": status,
    }
    return db_conn.execute(ADD_SENTENCE, params).scalar_one()


def test_story_without_first_sentence_is_hidden(client, seed):
    # seed의 스토리는 문장이 하나도 없음 → 목록에 안 나오고, 직접 들어가도 404
    body = client.get("/api/stories").json()
    assert body["items"] == []
    assert body["total"] == 0

    response = client.get(f"/api/stories/{seed['story']}")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "STORY_NOT_FOUND"


def test_create_story_saves_title_and_first_sentence(client):
    created = create_story(client, title="  비 오는 날  ", content=" 편지가 왔다. ")

    story, sentence = created["story"], created["sentence"]
    assert story["title"] == "비 오는 날"  # 앞뒤 공백은 자동으로 지움
    assert story["first_sentence"] == "편지가 왔다."
    assert story["first_sentence_id"] == sentence["id"]
    assert story["first_sentence_status"] == "active"
    assert story["author_count"] == 1
    assert story["max_depth"] == 0
    assert sentence["depth"] == 0
    assert sentence["parent_id"] is None
    assert sentence["author_nickname"] == "author"

    listed = client.get("/api/stories").json()
    assert [s["id"] for s in listed["items"]] == [story["id"]]
    assert client.get(f"/api/stories/{story['id']}").json() == story


@pytest.mark.parametrize(
    ("title", "content"),
    [
        ("   ", "문장"),
        ("제목", "   "),
        ("가" * 51, "문장"),
        ("제목", "가" * 101),
        ("제목", "첫 줄\n둘째 줄"),
    ],
    ids=["blank-title", "blank-content", "title-51", "content-101", "newline"],
)
def test_create_story_rejects_invalid_input(client, title, content):
    response = client.post("/api/stories", json={"title": title, "content": content})

    assert response.status_code == 422


def test_create_story_needs_login(client, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)

    response = client.post("/api/stories", json={"title": "제목", "content": "문장"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


def test_story_list_sort_and_pages(client, db_conn, seed):
    shallow = create_story(client, title="얕은 스토리")["story"]["id"]
    deep_created = create_story(client, title="깊은 스토리")
    deep = deep_created["story"]["id"]
    first = add_sentence(db_conn, seed, deep, "둘째 문장", deep_created["sentence"]["id"], 1)
    add_sentence(db_conn, seed, deep, "셋째 문장", first, 2)

    def ids(query):
        return [s["id"] for s in client.get(f"/api/stories?{query}").json()["items"]]

    assert ids("sort=deepest") == [deep, shallow]
    assert ids("sort=shallowest") == [shallow, deep]
    assert ids("sort=latest") == [deep, shallow]
    assert ids("sort=oldest") == [shallow, deep]

    page2 = client.get("/api/stories?sort=latest&size=1&page=2").json()
    assert [s["id"] for s in page2["items"]] == [shallow]
    assert page2["total"] == 2
    assert client.get(f"/api/stories/{deep}").json()["max_depth"] == 2
    assert client.get("/api/stories?sort=unknown").status_code == 422
    assert client.get("/api/stories?size=51").status_code == 422


def test_folded_first_sentence_is_hidden(client, db_conn):
    # 신고로 접힌 첫 문장은 내용을 보내지 않음 → 카드엔 "신고 처리된 문장입니다."만 (D-69)
    created = create_story(client, content="신고가 쌓일 첫 문장")
    db_conn.execute(
        text("UPDATE sentences SET status = 'folded' WHERE id = :id"),
        {"id": created["sentence"]["id"]},
    )

    story = client.get(f"/api/stories/{created['story']['id']}").json()

    assert story["first_sentence"] is None
    assert story["first_sentence_status"] == "folded"


def test_story_with_removed_first_sentence_is_hidden(client, db_conn):
    created = create_story(client)
    db_conn.execute(
        text("UPDATE sentences SET status = 'removed' WHERE id = :id"),
        {"id": created["sentence"]["id"]},
    )

    assert client.get(f"/api/stories/{created['story']['id']}").status_code == 404
    assert client.get("/api/stories").json()["total"] == 0
