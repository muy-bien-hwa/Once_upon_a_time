"""기록 API (docs 07 #9)"""

from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, :content, :depth) RETURNING id"
)


def test_record_is_empty_without_stories(client):
    # seed의 스토리는 첫 문장이 없어서 보이지 않음 → 기록도 없음
    assert client.get("/api/stats/record").json()["most_authors_story"] is None


def test_record_picks_story_with_most_authors(client, db_conn, seed):
    client.post("/api/stories", json={"title": "작가 1명", "content": "첫 문장이다."})
    crowded = client.post(
        "/api/stories", json={"title": "작가 2명", "content": "첫 문장이다."}
    ).json()
    db_conn.execute(
        ADD_SENTENCE,
        {
            "story": crowded["story"]["id"],
            "parent": crowded["sentence"]["id"],
            "author": seed["voter"],
            "content": "다른 작가가 이어 쓴 문장이다.",
            "depth": 1,
        },
    )

    record = client.get("/api/stats/record").json()["most_authors_story"]

    assert record["id"] == crowded["story"]["id"]
    assert record["author_count"] == 2
