"""기록·Hot API (docs 07 #9~#11)"""

from datetime import timedelta

from sqlalchemy import text

from app.timeutil import kst_today_start

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, :content, :depth) RETURNING id"
)
RECOMMEND = text(
    "INSERT INTO story_recommendations (user_id, story_id, created_at) "
    "VALUES (:user, :story, :when)"
)
VOTE = text(
    "INSERT INTO sentence_votes (user_id, sentence_id, value, created_at) "
    "VALUES (:user, :sentence, :value, :when)"
)
ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :nickname) RETURNING id"
)

TODAY = kst_today_start() + timedelta(minutes=1)
THIS_WEEK = kst_today_start() - timedelta(days=3)
THIS_MONTH = kst_today_start() - timedelta(days=20)
# 월간(30일)에도 안 잡히는 오래된 시각
LONG_AGO = kst_today_start() - timedelta(days=40)


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


def readers(db_conn, count: int) -> list[int]:
    """추천·투표를 남길 유저 여러 명 (1인 1표라 사람 수만큼 필요)"""
    return [
        db_conn.execute(ADD_USER, {"sub": f"reader-{i}", "nickname": f"독자{i}"}).scalar_one()
        for i in range(count)
    ]


def test_top_stories_counts_each_period(client, db_conn):
    quiet = client.post("/api/stories", json={"title": "조용한", "content": "첫 문장이다."}).json()
    popular = client.post("/api/stories", json={"title": "인기", "content": "첫 문장이다."}).json()
    people = readers(db_conn, 4)
    for user, when in zip(people[:3], (TODAY, THIS_WEEK, THIS_MONTH), strict=True):
        db_conn.execute(RECOMMEND, {"user": user, "story": popular["story"]["id"], "when": when})
    # 30일보다 오래된 추천은 월간에도 안 잡혀야 함
    db_conn.execute(RECOMMEND, {"user": people[3], "story": quiet["story"]["id"], "when": LONG_AGO})

    body = client.get("/api/stats/top-stories").json()

    assert [(item["story"]["title"], item["recommend_count"]) for item in body["day"]] == [
        ("인기", 1)
    ]
    assert body["week"][0]["recommend_count"] == 2
    assert body["month"][0]["recommend_count"] == 3
    # 오래된 추천만 있는 스토리는 어느 기간에도 안 나옴
    assert all(item["story"]["title"] != "조용한" for period in body.values() for item in period)


def test_top_sentences_skips_hidden_and_non_positive(client, db_conn, seed):
    liked = client.post(
        "/api/stories", json={"title": "추천받은", "content": "좋은 문장이다."}
    ).json()
    disliked = client.post(
        "/api/stories", json={"title": "비추천", "content": "아쉬운 문장이다."}
    ).json()
    hidden = client.post("/api/stories", json={"title": "숨긴", "content": "숨긴 첫 문장."}).json()
    buried = db_conn.execute(
        ADD_SENTENCE,
        {
            "story": hidden["story"]["id"],
            "parent": hidden["sentence"]["id"],
            "author": seed["author"],
            "content": "숨긴 스토리 안의 문장이다.",
            "depth": 1,
        },
    ).scalar_one()
    # 첫 문장을 숨기면 스토리 전체가 목록에서 빠짐 → Hot에도 나오면 안 됨
    db_conn.execute(
        text("UPDATE sentences SET status = 'removed' WHERE id = :id"),
        {"id": hidden["sentence"]["id"]},
    )

    people = readers(db_conn, 4)
    db_conn.execute(
        VOTE, {"user": people[0], "sentence": liked["sentence"]["id"], "value": 1, "when": TODAY}
    )
    db_conn.execute(VOTE, {"user": people[1], "sentence": buried, "value": 1, "when": TODAY})
    # 추천 1 · 비추천 1 → 합계 0이라 Top에 오르면 안 됨
    db_conn.execute(
        VOTE, {"user": people[2], "sentence": disliked["sentence"]["id"], "value": 1, "when": TODAY}
    )
    db_conn.execute(
        VOTE,
        {"user": people[3], "sentence": disliked["sentence"]["id"], "value": -1, "when": TODAY},
    )

    day = client.get("/api/stats/top-sentences").json()["day"]

    assert [item["sentence"]["id"] for item in day] == [liked["sentence"]["id"]]
    assert day[0]["story"]["title"] == "추천받은"
    assert day[0]["vote_count"] == 1
