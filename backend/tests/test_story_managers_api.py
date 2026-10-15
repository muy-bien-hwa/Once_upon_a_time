"""스토리 작가 목록 · 관리자 · 글 고정 (D-91)"""

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, :content, 1) RETURNING id"
)
HAND_OVER = text("UPDATE stories SET creator_id = :user WHERE id = :id")
MAKE_MANAGER = text("INSERT INTO story_managers (story_id, user_id) VALUES (:story, :user)")


@pytest.fixture
def story(client, db_conn, seed):
    """로그인 유저가 시작하고, 다른 사람(voter)도 한 문장 보탠 스토리"""
    created = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    db_conn.execute(
        ADD_SENTENCE,
        {
            "story": created["story"]["id"],
            "parent": created["sentence"]["id"],
            "author": seed["voter"],
            "content": "다른 작가가 이어 쓴 문장이다.",
        },
    )
    return created["story"]


def authors(client, story_id: int):
    return client.get(f"/api/stories/{story_id}/authors").json()


def write_post(client, story_id: int, title: str = "글 제목"):
    return client.post(
        f"/api/stories/{story_id}/forum/posts", json={"title": title, "body": "본문이다."}
    ).json()


def test_author_list_shows_everyone_with_their_sentence_count(client, story, seed):
    body = authors(client, story["id"])

    # 창시자가 맨 위 (PM 결정 2026-10-15)
    assert [
        (item["nickname"], item["sentence_count"], item["is_creator"]) for item in body["items"]
    ] == [
        ("author", 1, True),
        ("voter", 1, False),
    ]
    # 스토리를 시작한 사람이라 권한을 줄 수 있고, 글도 고정할 수 있음
    assert (body["can_appoint"], body["can_pin"]) == (True, True)


def test_only_the_creator_sees_the_appoint_buttons(client, db_conn, story, seed):
    db_conn.execute(HAND_OVER, {"user": seed["voter"], "id": story["id"]})

    body = authors(client, story["id"])

    assert (body["can_appoint"], body["can_pin"]) == (False, False)


def test_creator_can_appoint_and_dismiss_a_manager(client, story, seed):
    appointed = client.put(f"/api/stories/{story['id']}/managers/{seed['voter']}").json()
    assert [item["is_manager"] for item in appointed["items"]] == [False, True]

    dismissed = client.delete(f"/api/stories/{story['id']}/managers/{seed['voter']}").json()
    assert [item["is_manager"] for item in dismissed["items"]] == [False, False]


def test_cannot_appoint_someone_who_never_wrote_here(client, db_conn, story):
    stranger = db_conn.execute(
        text(
            "INSERT INTO users (provider, provider_user_id, nickname) "
            "VALUES ('google', 'stranger', '구경꾼') RETURNING id"
        )
    ).scalar_one()

    response = client.put(f"/api/stories/{story['id']}/managers/{stranger}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NOT_STORY_AUTHOR"


def test_only_the_creator_can_appoint(client, db_conn, story, seed):
    db_conn.execute(HAND_OVER, {"user": seed["voter"], "id": story["id"]})

    response = client.put(f"/api/stories/{story['id']}/managers/{seed['author']}")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOT_STORY_CREATOR"


def test_creator_can_pin_a_post_and_it_goes_on_top(client, story):
    first = write_post(client, story["id"], "먼저 쓴 글")
    write_post(client, story["id"], "나중에 쓴 글")

    pinned = client.put(f"/api/forum/posts/{first['id']}/pin").json()

    assert pinned["pin_slot"] == 1
    titles = [
        item["title"]
        for item in client.get(f"/api/stories/{story['id']}/forum/posts").json()["items"]
    ]
    assert titles == ["먼저 쓴 글", "나중에 쓴 글"]


def test_third_pin_is_refused(client, story):
    for i in range(2):
        post = write_post(client, story["id"], f"고정 {i}")
        assert client.put(f"/api/forum/posts/{post['id']}/pin").status_code == 200
    third = write_post(client, story["id"], "세 번째")

    response = client.put(f"/api/forum/posts/{third['id']}/pin")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PIN_LIMIT"


def test_unpinning_frees_the_slot(client, story):
    post = write_post(client, story["id"])
    client.put(f"/api/forum/posts/{post['id']}/pin")

    unpinned = client.delete(f"/api/forum/posts/{post['id']}/pin").json()

    assert unpinned["pin_slot"] is None


def test_a_plain_author_cannot_pin(client, db_conn, story, seed):
    post = write_post(client, story["id"])
    # 스토리를 넘겨 주면 나는 그냥 참여 작가
    db_conn.execute(HAND_OVER, {"user": seed["voter"], "id": story["id"]})

    response = client.put(f"/api/forum/posts/{post['id']}/pin")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PIN_NOT_ALLOWED"


def test_appointed_manager_can_pin(client, db_conn, story, seed):
    post = write_post(client, story["id"])
    db_conn.execute(HAND_OVER, {"user": seed["voter"], "id": story["id"]})
    db_conn.execute(MAKE_MANAGER, {"story": story["id"], "user": seed["author"]})

    assert client.put(f"/api/forum/posts/{post['id']}/pin").status_code == 200


def test_post_tells_whether_i_can_pin(client, db_conn, story, seed):
    post = write_post(client, story["id"])
    assert client.get(f"/api/forum/posts/{post['id']}").json()["can_pin"] is True

    db_conn.execute(HAND_OVER, {"user": seed["voter"], "id": story["id"]})

    assert client.get(f"/api/forum/posts/{post['id']}").json()["can_pin"] is False
    assert client.get(f"/api/stories/{story['id']}/forum/posts").json()["can_pin"] is False


def test_creator_then_managers_then_contributors(client, db_conn, story, seed):
    """줄 순서: 창시자 → 관리자 → 많이 쓴 순 (PM 결정 2026-10-15)"""
    # voter가 문장을 더 써서 기여 1위가 되게 함
    root = db_conn.execute(
        text("SELECT id FROM sentences WHERE story_id = :id AND parent_id IS NULL"),
        {"id": story["id"]},
    ).scalar_one()
    for _ in range(3):
        db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story["id"],
                "parent": root,
                "author": seed["voter"],
                "content": "더 쓴 문장이다.",
            },
        )

    body = authors(client, story["id"])

    # 기여는 voter가 많지만 창시자(author)가 맨 위
    assert [item["nickname"] for item in body["items"]] == ["author", "voter"]
