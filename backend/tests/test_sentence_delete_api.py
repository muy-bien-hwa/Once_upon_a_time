"""문장 삭제 (F-09, D-06·D-47·D-92)

- 이어진 문장이 없으면 흔적 없이 / 있으면 "삭제된 문장" 자리만
- 첫 문장은 이어진 문장이 없을 때만 지울 수 있고, 지우면 스토리도 사라짐 (D-92)
"""

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, :content, :depth) RETURNING id"
)


@pytest.fixture
def story(client):
    """로그인 유저가 시작한 스토리 (첫 문장도 내 것)"""
    return client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()


def write(client, parent_id: int, content: str = "이어 쓴 문장이다."):
    return client.post(f"/api/sentences/{parent_id}/children", json={"content": content}).json()


def test_sentence_without_children_disappears(client, story):
    child = write(client, story["sentence"]["id"])

    body = client.delete(f"/api/sentences/{child['id']}")

    assert body.json() == {"status": "removed"}
    # 목록에서도 사라짐
    items = client.get(f"/api/sentences/{story['sentence']['id']}/children").json()["items"]
    assert items == []


def test_sentence_with_children_leaves_a_mark(client, story):
    middle = write(client, story["sentence"]["id"], "가운데 문장이다.")
    write(client, middle["id"], "뒤에 이어진 문장이다.")

    body = client.delete(f"/api/sentences/{middle['id']}")

    assert body.json() == {"status": "deleted"}
    # 자리는 남고 내용은 가려짐 (D-63)
    shown = client.get(f"/api/sentences/{story['sentence']['id']}/children").json()["items"][0]
    assert (shown["status"], shown["content"]) == ("deleted", None)
    # 뒷이야기는 그대로
    assert len(client.get(f"/api/sentences/{middle['id']}/children").json()["items"]) == 1


def test_root_without_children_takes_the_story_with_it(client, story):
    story_id = story["story"]["id"]

    body = client.delete(f"/api/sentences/{story['sentence']['id']}")

    assert body.json() == {"status": "removed"}
    # 스토리가 통째로 사라짐 (D-92)
    assert client.get(f"/api/stories/{story_id}").status_code == 404
    titles = [item["title"] for item in client.get("/api/stories").json()["items"]]
    assert "제목" not in titles


def test_root_with_children_cannot_be_deleted(client, story):
    write(client, story["sentence"]["id"])

    response = client.delete(f"/api/sentences/{story['sentence']['id']}")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ROOT_HAS_CHILDREN"


def test_root_is_deletable_again_after_the_only_child_goes(client, story):
    child = write(client, story["sentence"]["id"])
    client.delete(f"/api/sentences/{child['id']}")

    assert client.delete(f"/api/sentences/{story['sentence']['id']}").status_code == 200


def test_cannot_delete_someone_elses_sentence(client, db_conn, story, seed):
    child = write(client, story["sentence"]["id"])
    db_conn.execute(
        text("UPDATE sentences SET author_id = :other WHERE id = :id"),
        {"other": seed["voter"], "id": child["id"]},
    )

    response = client.delete(f"/api/sentences/{child['id']}")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "NOT_MY_SENTENCE"


def test_deleting_twice_is_refused(client, story):
    middle = write(client, story["sentence"]["id"])
    write(client, middle["id"])
    client.delete(f"/api/sentences/{middle['id']}")

    response = client.delete(f"/api/sentences/{middle['id']}")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ALREADY_DELETED"


def test_deleted_sentence_still_counts_for_the_daily_limit(client, story):
    """지운 문장도 하루 10문장에 포함 (지웠다 다시 쓰는 우회 방지, D-47·D-90)"""
    parent = story["sentence"]["id"]
    for _ in range(9):
        parent = write(client, parent)["id"]
    client.delete(f"/api/sentences/{parent}")

    response = client.post(
        f"/api/sentences/{story['sentence']['id']}/children", json={"content": "열한 번째다."}
    )

    assert response.status_code == 429


def test_author_count_keeps_deleted_writers(client, db_conn, story, seed):
    """지운 문장의 작가도 참여 작가 수에 남음 (D-47)"""
    added = db_conn.execute(
        ADD_SENTENCE,
        {
            "story": story["story"]["id"],
            "parent": story["sentence"]["id"],
            "author": seed["voter"],
            "content": "다른 사람이 쓴 문장이다.",
            "depth": 1,
        },
    ).scalar_one()
    db_conn.execute(text("UPDATE sentences SET status = 'deleted' WHERE id = :id"), {"id": added})

    assert client.get(f"/api/stories/{story['story']['id']}").json()["author_count"] == 2


def test_delete_needs_login(client, story, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    child = write(client, story["sentence"]["id"])
    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.clear()

    assert client.delete(f"/api/sentences/{child['id']}").status_code == 401
