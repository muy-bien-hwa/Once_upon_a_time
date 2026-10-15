"""포럼 글 (docs 07 포럼, F-17·D-42·D-91)"""

from datetime import timedelta

import pytest
from sqlalchemy import text

from app.timeutil import kst_today_start

ADD_COMMENT = text(
    "INSERT INTO forum_comments (post_id, author_id, body) "
    "VALUES (:post, :author, :body) RETURNING id"
)
ADD_VOTE = text(
    "INSERT INTO forum_post_votes (user_id, post_id, value) VALUES (:user, :post, :value)"
)
PIN = text("UPDATE forum_posts SET pin_slot = :slot WHERE id = :id")
OLDER = kst_today_start() - timedelta(days=2)


@pytest.fixture
def story(client):
    """글을 쓸 스토리 하나 (로그인 유저가 시작)"""
    return client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()


def write_post(client, story_id: int, title: str = "글 제목", **extra):
    return client.post(
        f"/api/stories/{story_id}/forum/posts",
        json={"title": title, "body": "글 본문이다.", **extra},
    )


def titles(client, story_id: int, sort: str = "new"):
    body = client.get(f"/api/stories/{story_id}/forum/posts?sort={sort}").json()
    return [item["title"] for item in body["items"]]


def test_new_post_comes_first(client, story):
    story_id = story["story"]["id"]
    write_post(client, story_id, "먼저 쓴 글")
    write_post(client, story_id, "나중에 쓴 글")

    assert titles(client, story_id) == ["나중에 쓴 글", "먼저 쓴 글"]


def test_pinned_post_stays_on_top(client, db_conn, story):
    story_id = story["story"]["id"]
    pinned = write_post(client, story_id, "고정될 글").json()
    write_post(client, story_id, "방금 쓴 글")
    db_conn.execute(PIN, {"slot": 1, "id": pinned["id"]})

    # 최신순이어도 고정글이 먼저
    assert titles(client, story_id) == ["고정될 글", "방금 쓴 글"]


def test_hot_sort_lifts_the_voted_post(client, db_conn, story, seed):
    story_id = story["story"]["id"]
    liked = write_post(client, story_id, "표를 받은 글").json()
    write_post(client, story_id, "방금 쓴 글")
    db_conn.execute(ADD_VOTE, {"user": seed["voter"], "post": liked["id"], "value": 1})

    assert titles(client, story_id, sort="hot")[0] == "표를 받은 글"
    # 최신순에서는 그대로 방금 쓴 글이 위
    assert titles(client, story_id)[0] == "방금 쓴 글"


def test_post_can_quote_a_sentence_of_the_story(client, story):
    first = story["sentence"]

    body = write_post(client, story["story"]["id"], quoted_sentence_id=first["id"]).json()

    assert body["quoted_sentence"] == {"id": first["id"], "content": first["content"]}


def test_cannot_quote_a_sentence_from_another_story(client, story):
    other = client.post(
        "/api/stories", json={"title": "다른 스토리", "content": "남의 첫 문장이다."}
    ).json()

    response = write_post(client, story["story"]["id"], quoted_sentence_id=other["sentence"]["id"])

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "QUOTE_NOT_FOUND"


def test_title_over_100_characters_is_refused(client, story):
    response = write_post(client, story["story"]["id"], "가" * 101)

    assert response.status_code == 422


def test_deleted_post_disappears_with_its_comments(client, db_conn, story, seed):
    story_id = story["story"]["id"]
    post = write_post(client, story_id, "지울 글").json()
    comment_id = db_conn.execute(
        ADD_COMMENT, {"post": post["id"], "author": seed["voter"], "body": "댓글이다."}
    ).scalar_one()

    assert client.delete(f"/api/forum/posts/{post['id']}").status_code == 200

    assert titles(client, story_id) == []
    gone = client.get(f"/api/forum/posts/{post['id']}")
    assert gone.status_code == 404
    assert gone.json()["detail"]["message"] == "삭제된 글입니다"
    # 글이 사라지면 댓글도 함께 사라짐 (D-91)
    status = db_conn.execute(
        text("SELECT status FROM forum_comments WHERE id = :id"), {"id": comment_id}
    ).scalar_one()
    assert status == "removed"


def test_only_the_author_can_delete(client, db_conn, story, seed):
    post = write_post(client, story["story"]["id"]).json()
    db_conn.execute(
        text("UPDATE forum_posts SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": post["id"]},
    )

    response = client.delete(f"/api/forum/posts/{post['id']}")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOT_MY_POST"


def test_missing_post_says_it_does_not_exist(client):
    response = client.get("/api/forum/posts/10000000")

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "없는 글이에요"


def test_writing_needs_login(client, story, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.clear()

    assert write_post(client, story["story"]["id"]).status_code == 401


def test_eleventh_post_today_is_refused(client, db_conn, story):
    story_id = story["story"]["id"]
    for i in range(10):
        assert write_post(client, story_id, f"글 {i}").status_code == 201

    response = write_post(client, story_id, "열한 번째")

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "DAILY_POST_LIMIT"


def test_yesterdays_posts_do_not_count(client, db_conn, story):
    story_id = story["story"]["id"]
    for i in range(10):
        write_post(client, story_id, f"글 {i}")
    db_conn.execute(text("UPDATE forum_posts SET created_at = :when"), {"when": OLDER})

    assert write_post(client, story_id, "오늘 첫 글").status_code == 201


def test_story_carries_the_post_count(client, story):
    story_id = story["story"]["id"]
    write_post(client, story_id)

    assert client.get(f"/api/stories/{story_id}").json()["post_count"] == 1


def test_forum_of_a_missing_story_is_404(client):
    assert client.get("/api/stories/10000000/forum/posts").status_code == 404
