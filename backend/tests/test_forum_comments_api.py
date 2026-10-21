"""포럼 댓글 (F-17·D-91)

답글의 답글도 같은 줄(2단)에 놓고, 누구에게 한 말인지는 @닉네임으로 알려 줌
"""

import pytest
from sqlalchemy import text

ADD_COMMENT = text(
    "INSERT INTO forum_comments (post_id, author_id, body) VALUES (:post, :author, :body)"
)


@pytest.fixture
def post(client):
    """댓글을 달 글 하나"""
    story = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    return client.post(
        f"/api/stories/{story['story']['id']}/forum/posts",
        json={"title": "글 제목", "body": "글 본문이다."},
    ).json()


def comment(client, post_id: int, body: str, parent_id: int | None = None):
    payload: dict = {"body": body}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    return client.post(f"/api/forum/posts/{post_id}/comments", json=payload)


def comments(client, post_id: int):
    return client.get(f"/api/forum/posts/{post_id}/comments").json()["items"]


def test_top_level_comment_has_no_parent_and_no_mention(client, post):
    body = comment(client, post["id"], "댓글이다.").json()

    assert (body["parent_id"], body["reply_to_nickname"]) == (None, None)
    assert [item["body"] for item in comments(client, post["id"])] == ["댓글이다."]


def test_reply_hangs_under_the_comment_and_mentions_its_author(client, db_conn, post, seed):
    first = comment(client, post["id"], "맨 위 댓글이다.").json()
    # 다른 사람이 쓴 댓글에 답글을 달아야 @가 의미 있음
    db_conn.execute(
        text("UPDATE forum_comments SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": first["id"]},
    )

    reply = comment(client, post["id"], "답글이다.", parent_id=first["id"]).json()

    assert reply["parent_id"] == first["id"]
    assert reply["reply_to_nickname"] == "voter"


def test_reply_to_a_reply_stays_on_the_same_level(client, post):
    first = comment(client, post["id"], "맨 위 댓글이다.").json()
    reply = comment(client, post["id"], "답글이다.", parent_id=first["id"]).json()

    deeper = comment(client, post["id"], "답글의 답글이다.", parent_id=reply["id"]).json()

    # 한 칸 더 들어가지 않고 맨 위 댓글에 나란히 붙음 (D-91)
    assert deeper["parent_id"] == first["id"]
    # 대신 방금 답한 사람을 부름
    assert deeper["reply_to_nickname"] == "author"


def test_mention_follows_the_new_nickname(client, db_conn, post, seed):
    first = comment(client, post["id"], "맨 위 댓글이다.").json()
    db_conn.execute(
        text("UPDATE forum_comments SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": first["id"]},
    )
    comment(client, post["id"], "답글이다.", parent_id=first["id"])

    db_conn.execute(
        text("UPDATE users SET nickname = '바뀐이름' WHERE id = :id"), {"id": seed["voter"]}
    )

    reply = comments(client, post["id"])[1]
    assert reply["reply_to_nickname"] == "바뀐이름"


def test_deleting_a_top_comment_takes_its_replies(client, post):
    first = comment(client, post["id"], "맨 위 댓글이다.").json()
    comment(client, post["id"], "답글이다.", parent_id=first["id"])

    assert client.delete(f"/api/forum/comments/{first['id']}").status_code == 200

    assert comments(client, post["id"]) == []


def test_deleting_a_reply_keeps_the_comment(client, post):
    first = comment(client, post["id"], "맨 위 댓글이다.").json()
    reply = comment(client, post["id"], "답글이다.", parent_id=first["id"]).json()

    client.delete(f"/api/forum/comments/{reply['id']}")

    assert [item["body"] for item in comments(client, post["id"])] == ["맨 위 댓글이다."]


def test_only_the_author_can_delete_a_comment(client, db_conn, post, seed):
    mine = comment(client, post["id"], "댓글이다.").json()
    db_conn.execute(
        text("UPDATE forum_comments SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": mine["id"]},
    )

    response = client.delete(f"/api/forum/comments/{mine['id']}")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOT_MY_COMMENT"


def test_comment_over_1000_characters_is_refused(client, post):
    assert comment(client, post["id"], "가" * 1001).status_code == 422


def test_cannot_comment_on_a_deleted_post(client, post):
    client.delete(f"/api/forum/posts/{post['id']}")

    response = comment(client, post["id"], "댓글이다.")

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "삭제된 글입니다"


def test_fifty_first_comment_today_is_refused(client, db_conn, post, seed):
    for _ in range(50):
        db_conn.execute(
            ADD_COMMENT, {"post": post["id"], "author": seed["author"], "body": "미리 쓴 댓글."}
        )

    response = comment(client, post["id"], "쉰한 번째다.")

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "DAILY_COMMENT_LIMIT"


def test_comment_needs_login(client, post):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert comment(client, post["id"], "댓글이다.").status_code == 401
