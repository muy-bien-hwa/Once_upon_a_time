"""하루 제한 (F-08, D-49·D-90)

하루 기준은 한국 시간 0시 / 지운 문장도 셈
"""

from datetime import timedelta

from sqlalchemy import text

from app.timeutil import kst_today_start

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status, created_at) "
    "VALUES (:story, :parent, :author, :content, :depth, :status, :when) RETURNING id"
)
TODAY = kst_today_start() + timedelta(minutes=1)
YESTERDAY = kst_today_start() - timedelta(hours=1)


def open_story(client, title: str = "제목"):
    return client.post("/api/stories", json={"title": title, "content": "첫 문장이다."})


def write(client, parent_id: int):
    return client.post(
        f"/api/sentences/{parent_id}/children", json={"content": "이어 쓴 문장이다."}
    )


def add_rows(db_conn, story_id: int, root_id: int, author_id: int, count: int, status: str, when):
    """화면을 거치지 않고 문장을 직접 넣음 (어제 쓴 글·지운 글을 만들려고)"""
    for _ in range(count):
        db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story_id,
                "parent": root_id,
                "author": author_id,
                "content": "미리 넣어 둔 문장이다.",
                "depth": 1,
                "status": status,
                "when": when,
            },
        )


def test_sixth_story_today_is_refused(client, db_conn, seed):
    # seed 스토리도 "오늘 연 스토리"로 세므로 어제 것으로 돌려놓고 시작
    db_conn.execute(
        text("UPDATE stories SET created_at = :when WHERE id = :id"),
        {"when": YESTERDAY, "id": seed["story"]},
    )

    for i in range(5):
        assert open_story(client, f"스토리 {i}").status_code == 201

    response = open_story(client, "여섯 번째")

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "DAILY_STORY_LIMIT"


def test_eleventh_sentence_in_one_story_is_refused(client):
    # 첫 문장도 오늘 쓴 1문장으로 셈 → 이어 쓰기 9번이면 10문장
    parent = open_story(client).json()["sentence"]["id"]
    for _ in range(9):
        parent = write(client, parent).json()["id"]

    response = write(client, parent)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "DAILY_SENTENCE_LIMIT"


def test_each_story_has_its_own_count(client):
    parent = open_story(client, "꽉 찬 스토리").json()["sentence"]["id"]
    for _ in range(9):
        parent = write(client, parent).json()["id"]
    assert write(client, parent).status_code == 429

    other = open_story(client, "다른 스토리").json()["sentence"]["id"]

    assert write(client, other).status_code == 201


def test_yesterday_does_not_count(client, db_conn, seed):
    story = open_story(client).json()
    root = story["sentence"]["id"]
    add_rows(db_conn, story["story"]["id"], root, seed["author"], 10, "active", YESTERDAY)

    assert write(client, root).status_code == 201


def test_deleted_sentences_still_count(client, db_conn, seed):
    story = open_story(client).json()
    root = story["sentence"]["id"]
    # 오늘 쓴 10문장(첫 문장 + 9) 중 9개를 지운 상태로 둠
    add_rows(db_conn, story["story"]["id"], root, seed["author"], 9, "deleted", TODAY)

    response = write(client, root)

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "DAILY_SENTENCE_LIMIT"


def test_other_peoples_sentences_do_not_count(client, db_conn, seed):
    story = open_story(client).json()
    root = story["sentence"]["id"]
    add_rows(db_conn, story["story"]["id"], root, seed["voter"], 10, "active", TODAY)

    assert write(client, root).status_code == 201
