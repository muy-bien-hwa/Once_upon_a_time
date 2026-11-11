"""인용할 문장 찾기 (#38, D-102)

커뮤니티 글쓰기에서 그 스토리의 문장을 낱말로 찾아 인용함
- 인용할 수 있는 문장(보이는 문장)만 나옴 / 다른 스토리 문장은 안 나옴
"""

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, :parent, :author, :content, 1, :status) RETURNING id"
)


@pytest.fixture
def story(client, db_conn, seed):
    """스토리 하나 + 이어 쓴 문장 넷 (보임 둘 · 지움 · 접힘)"""
    made = client.post(
        "/api/stories", json={"title": "달을 주운 우체부", "content": "우체부가 살았다."}
    ).json()
    root = made["sentence"]["id"]

    def add(content: str, status: str = "active", author: str = "author") -> int:
        params = {
            "story": made["story"]["id"],
            "parent": root,
            "author": seed[author],
            "content": content,
            "status": status,
        }
        return db_conn.execute(ADD_SENTENCE, params).scalar_one()

    return {
        "id": made["story"]["id"],
        "root": root,
        "moon": add("그는 달 한 조각을 주웠다."),
        "moon_by_voter": add("달은 손바닥만 했다.", author="voter"),
        "deleted": add("달을 지운 문장이다.", "deleted"),
        "folded": add("달이 접힌 문장이다.", "folded"),
    }


def search(client, story_id: int, q: str):
    return client.get(f"/api/stories/{story_id}/sentences", params={"q": q})


def test_finds_visible_sentences_only(client, story):
    response = search(client, story["id"], "달")
    assert response.status_code == 200, response.text
    found = {item["id"] for item in response.json()["items"]}
    # 지운 문장·접힌 문장은 인용할 수 없으므로 찾기에도 안 나옴
    assert found == {story["moon"], story["moon_by_voter"]}


def test_shows_content_and_author(client, story):
    items = search(client, story["id"], "손바닥").json()["items"]
    assert items == [
        {"id": story["moon_by_voter"], "content": "달은 손바닥만 했다.", "author_nickname": "voter"}
    ]


def test_first_sentence_can_be_found(client, story):
    items = search(client, story["id"], "우체부가").json()["items"]
    assert [item["id"] for item in items] == [story["root"]]


def test_other_story_is_not_searched(client, story):
    other = client.post(
        "/api/stories", json={"title": "다른 이야기", "content": "달이 둘인 마을이 있었다."}
    ).json()
    found = {item["id"] for item in search(client, story["id"], "달").json()["items"]}
    assert other["sentence"]["id"] not in found


def test_percent_is_searched_as_a_letter(client, story):
    # %를 쳐도 "아무 글자"로 풀리지 않음 → 문장에 %가 없으니 아무것도 안 나옴
    assert search(client, story["id"], "%").json()["items"] == []


def test_blank_query_finds_nothing(client, story):
    body = search(client, story["id"], "   ").json()
    assert body["items"] == []
    assert body["total"] == 0


def test_query_is_required(client, story):
    assert client.get(f"/api/stories/{story['id']}/sentences").status_code == 422


def test_ten_at_a_time_and_more_on_next_page(client, db_conn, seed, story):
    for number in range(12):
        db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story["id"],
                "parent": story["root"],
                "author": seed["author"],
                "content": f"별 {number}개가 떴다.",
                "status": "active",
            },
        )
    first = search(client, story["id"], "별").json()
    assert len(first["items"]) == 10
    # [더 보기]가 남은 개수를 알 수 있게 전체 수도 함께
    assert (first["page"], first["size"], first["total"]) == (1, 10, 12)

    second = client.get(
        f"/api/stories/{story['id']}/sentences", params={"q": "별", "page": 2}
    ).json()
    assert len(second["items"]) == 2
    # 두 쪽을 합치면 겹치지 않고 12개 전부
    ids = [item["id"] for item in first["items"] + second["items"]]
    assert len(set(ids)) == 12


def test_page_must_start_at_one(client, story):
    response = client.get(f"/api/stories/{story['id']}/sentences", params={"q": "달", "page": 0})
    assert response.status_code == 422


def test_hidden_story_is_not_found(client, db_conn, story):
    # 스토리째 숨겨졌으면(첫 문장이 removed) 없는 스토리와 같음
    db_conn.execute(
        text("UPDATE sentences SET status = 'removed' WHERE id = :id"), {"id": story["root"]}
    )
    response = search(client, story["id"], "달")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "STORY_NOT_FOUND"


def test_found_sentence_can_be_quoted(client, story):
    # 찾기에 나온 문장은 그대로 인용해서 글을 올릴 수 있어야 함
    found = search(client, story["id"], "조각").json()["items"][0]
    response = client.post(
        f"/api/stories/{story['id']}/forum/posts",
        json={
            "title": "이 문장 좋아요",
            "body": "달 조각이라니.",
            "quoted_sentence_id": found["id"],
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["quoted_sentence"] == {"id": found["id"], "content": found["content"]}
