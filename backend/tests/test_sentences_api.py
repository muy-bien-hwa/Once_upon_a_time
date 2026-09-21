"""문장 API (docs 07 #6~#8)"""

import pytest
from sqlalchemy import text

SET_STATUS = text("UPDATE sentences SET status = :status WHERE id = :id")


def create_story(client, content="옛날 옛적에 고양이가 살았다."):
    response = client.post("/api/stories", json={"title": "고양이", "content": content})
    assert response.status_code == 201, response.text
    return response.json()["sentence"]["id"]


def write(client, parent_id, content):
    return client.post(f"/api/sentences/{parent_id}/children", json={"content": content})


def write_ok(client, parent_id, content):
    response = write(client, parent_id, content)
    assert response.status_code == 201, response.text
    return response.json()


def test_write_child_sentence(client):
    root = create_story(client)

    child = write_ok(client, root, " 고양이는 별을 셌다. ")

    assert child["parent_id"] == root
    assert child["depth"] == 1
    assert child["content"] == "고양이는 별을 셌다."
    assert child["author_nickname"] == "author"
    assert child["child_count"] == 0


def test_path_goes_from_first_sentence_to_current(client):
    root = create_story(client)
    child = write_ok(client, root, "둘째 문장")["id"]
    grandchild = write_ok(client, child, "셋째 문장")["id"]

    body = client.get(f"/api/sentences/{grandchild}/path").json()

    assert body["story"]["title"] == "고양이"
    assert [i["id"] for i in body["items"]] == [root, child, grandchild]
    assert [i["depth"] for i in body["items"]] == [0, 1, 2]


def test_children_list_and_sort(client):
    root = create_story(client)
    first = write_ok(client, root, "먼저 쓴 문장")["id"]
    second = write_ok(client, root, "나중에 쓴 문장")["id"]

    latest = client.get(f"/api/sentences/{root}/children?sort=latest").json()["items"]
    default = client.get(f"/api/sentences/{root}/children").json()["items"]

    assert [i["id"] for i in latest] == [second, first]
    assert sorted(i["id"] for i in default) == sorted([first, second])
    assert client.get(f"/api/sentences/{root}/children?sort=unknown").status_code == 422


def test_missing_sentence_is_404(client):
    for response in (
        client.get("/api/sentences/999999/path"),
        client.get("/api/sentences/999999/children"),
        write(client, 999999, "문장"),
    ):
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SENTENCE_NOT_FOUND"


def test_path_through_removed_sentence_is_404(client, db_conn):
    root = create_story(client)
    hidden = write_ok(client, root, "숨길 문장")["id"]
    child = write_ok(client, hidden, "그 아래 문장")["id"]
    db_conn.execute(SET_STATUS, {"status": "removed", "id": hidden})

    assert client.get(f"/api/sentences/{child}/path").status_code == 404


@pytest.mark.parametrize(
    ("status", "code"),
    [("deleted", "PARENT_DELETED"), ("folded", "PARENT_FOLDED")],
)
def test_cannot_write_after_deleted_or_folded(client, db_conn, status, code):
    # 삭제된 문장(D-50)·신고로 접힌 문장(D-70) 뒤에는 이어 쓸 수 없음
    root = create_story(client)
    parent = write_ok(client, root, "곧 사라질 문장")["id"]
    db_conn.execute(SET_STATUS, {"status": status, "id": parent})

    response = write(client, parent, "이어 쓰기 시도")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == code


def test_folded_sentence_children_stay_readable_and_writable(client, db_conn):
    # 접힌 문장 아래 이미 있는 문장은 보이고, 그 문장 뒤로는 이어 쓸 수 있음 (D-70)
    root = create_story(client)
    folded = write_ok(client, root, "신고될 문장")["id"]
    below = write_ok(client, folded, "그 아래 문장")["id"]
    db_conn.execute(SET_STATUS, {"status": "folded", "id": folded})

    path = client.get(f"/api/sentences/{below}/path").json()["items"]
    children = client.get(f"/api/sentences/{folded}/children").json()["items"]

    assert path[1]["status"] == "folded"
    assert path[1]["content"] is None  # 접힌 문장은 내용을 보내지 않음 (D-69)
    assert [i["id"] for i in children] == [below]
    assert write(client, below, "계속 이어 쓰기").status_code == 201


def test_write_needs_login(client, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    root = create_story(client)
    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)

    response = write(client, root, "문장")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"


@pytest.mark.parametrize(
    "content",
    ["   ", "가" * 101, "첫 줄\n둘째 줄"],
    ids=["blank", "101-chars", "newline"],
)
def test_write_rejects_invalid_content(client, content):
    root = create_story(client)

    assert write(client, root, content).status_code == 422
