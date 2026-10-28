"""마이페이지·작가 화면 (#34~#37, D-95)

- 내 화면: 지운 문장·접힌 문장도 목록에 나오되 본문은 비어 있음
- 작가 화면: 보이는 문장만 / 가입 시점은 연월까지만 / 없는 닉네임도 탈퇴한 사람도 똑같이 404
- 검색은 보이는 문장 안에서만
"""

from datetime import datetime

import pytest
from sqlalchemy import text

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, :parent, :author, :content, 1, :status) RETURNING id"
)
ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :nickname) RETURNING id"
)
ADD_VOTE = text(
    "INSERT INTO sentence_votes (user_id, sentence_id, value) VALUES (:user, :sentence, 1)"
)


@pytest.fixture
def mine(client, db_conn, seed):
    """내가 시작한 스토리 + 내가 이어 쓴 문장 셋 (보임·지움·접힘)"""
    story = client.post(
        "/api/stories", json={"title": "등대가 꺼진 밤", "content": "첫 문장이다."}
    ).json()
    root = story["sentence"]["id"]

    def add(content: str, status: str = "active") -> int:
        return db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story["story"]["id"],
                "parent": root,
                "author": seed["author"],
                "content": content,
                "status": status,
            },
        ).scalar_one()

    return {
        "story": story["story"]["id"],
        "root": root,
        "live": add("등대지기는 노랫소리를 들었다."),
        "deleted": add("지운 문장이다.", "deleted"),
        "folded": add("접힌 문장이다.", "folded"),
    }


def vote(db_conn, sentence_id: int, voters: int) -> None:
    for number in range(voters):
        user = db_conn.execute(
            ADD_USER, {"sub": f"fan-{sentence_id}-{number}", "nickname": f"팬{sentence_id}{number}"}
        ).scalar_one()
        db_conn.execute(ADD_VOTE, {"user": user, "sentence": sentence_id})


# ── #34 내 요약 ──


def test_summary_counts_what_the_list_shows(client, db_conn, mine):
    vote(db_conn, mine["live"], 2)

    summary = client.get("/api/me/summary").json()

    # 첫 문장 + 보이는 문장 + 지운 문장 + 접힌 문장
    assert summary["sentence_count"] == 4
    assert summary["live_sentence_count"] == 2
    assert summary["story_count"] == 1
    assert summary["received_up_count"] == 2


def test_summary_tells_when_i_joined(client, db_conn, seed):
    joined = db_conn.execute(
        text("SELECT created_at FROM users WHERE id = :id"), {"id": seed["author"]}
    ).scalar_one()

    # 같은 시각인지로 비교 (글자로 비교하면 시간대 때문에 날짜가 하루 어긋날 수 있음)
    assert datetime.fromisoformat(client.get("/api/me/summary").json()["joined_at"]) == joined


def test_summary_needs_login(client):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert client.get("/api/me/summary").status_code == 401


# ── #35 내 문장 ──


def test_my_sentences_are_newest_first(client, mine):
    listing = client.get("/api/me/sentences").json()

    assert listing["total"] == 4
    assert [item["id"] for item in listing["items"]] == [
        mine["folded"],
        mine["deleted"],
        mine["live"],
        mine["root"],
    ]


def test_my_sentences_carry_the_story_title(client, mine):
    first = client.get("/api/me/sentences?sort=latest").json()["items"][-1]

    assert first["story_title"] == "등대가 꺼진 밤"
    assert first["content"] == "첫 문장이다."


def test_hidden_sentences_keep_their_place_but_not_their_text(client, mine):
    items = {item["id"]: item for item in client.get("/api/me/sentences").json()["items"]}

    assert items[mine["deleted"]]["content"] is None
    assert items[mine["deleted"]]["status"] == "deleted"
    assert items[mine["folded"]]["content"] is None
    assert items[mine["folded"]]["status"] == "folded"


def test_search_also_finds_my_hidden_sentences(client, mine):
    """내가 쓴 내 문장이므로 지운 것·접힌 것도 찾아 줌 (본문은 여전히 비어 있음)"""
    found = client.get("/api/me/sentences?q=문장이다").json()

    assert {item["id"] for item in found["items"]} == {
        mine["root"],
        mine["deleted"],
        mine["folded"],
    }
    assert next(i for i in found["items"] if i["id"] == mine["folded"])["content"] is None


def test_filtering_by_status(client, mine):
    only_deleted = client.get("/api/me/sentences?status=deleted").json()

    assert [item["id"] for item in only_deleted["items"]] == [mine["deleted"]]
    assert only_deleted["total"] == 1


def test_filtering_inside_a_search(client, mine):
    """예: '문장이다'로 찾은 것 중에서 지운 것만"""
    found = client.get("/api/me/sentences?q=문장이다&status=deleted").json()

    assert [item["id"] for item in found["items"]] == [mine["deleted"]]


def test_counts_follow_the_search(client, mine):
    whole = client.get("/api/me/sentences").json()["counts"]
    assert whole == {"all": 4, "active": 2, "deleted": 1, "folded": 1}

    searched = client.get("/api/me/sentences?q=지운").json()["counts"]
    assert searched == {"all": 1, "active": 0, "deleted": 1, "folded": 0}


def test_an_author_list_has_no_counts(client, mine):
    """작가 화면은 보이는 문장뿐이라 거를 것이 없음"""
    assert client.get("/api/users/author/sentences").json()["counts"] is None


def test_search_takes_percent_as_a_letter(client, mine):
    assert client.get("/api/me/sentences?q=%25").json()["total"] == 0


def test_sorting_by_votes(client, db_conn, mine):
    vote(db_conn, mine["live"], 3)

    top = client.get("/api/me/sentences?sort=votes").json()["items"][0]

    assert top["id"] == mine["live"]
    assert top["up_count"] == 3


def test_my_sentences_come_in_pages(client, mine):
    page = client.get("/api/me/sentences?page=2&size=3").json()

    assert page["total"] == 4
    assert len(page["items"]) == 1
    assert page["page"] == 2


def test_my_sentences_need_login(client):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert client.get("/api/me/sentences").status_code == 401


# ── #36·#37 작가 화면 ──


def test_anyone_can_see_an_author(client, db_conn, mine):
    vote(db_conn, mine["live"], 5)

    author = client.get("/api/users/author").json()

    assert author["nickname"] == "author"
    # 지운 문장·접힌 문장은 빼고 셈 (내 화면과 다른 점)
    assert author["sentence_count"] == 2
    assert author["story_count"] == 1
    assert author["received_up_count"] == 5


def test_an_author_page_shows_the_month_only(client, mine):
    assert len(client.get("/api/users/author").json()["joined_month"]) == len("2026-05")


def test_an_author_list_leaves_out_hidden_sentences(client, mine):
    listing = client.get("/api/users/author/sentences").json()

    assert [item["id"] for item in listing["items"]] == [mine["live"], mine["root"]]
    assert listing["total"] == 2


def test_an_unknown_nickname_is_not_found(client):
    response = client.get("/api/users/없는사람")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "USER_NOT_FOUND"


def test_a_withdrawn_author_looks_the_same_as_an_unknown_one(client, mine):
    """탈퇴했다는 사실 자체를 알려 주지 않음"""
    client.delete("/api/me")

    assert client.get("/api/users/author").status_code == 404
    assert client.get("/api/users/author/sentences").status_code == 404


def test_an_author_page_works_without_logging_in(client, mine):
    from app.deps import get_current_user, get_optional_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_optional_user)
    client.cookies.clear()

    assert client.get("/api/users/author").status_code == 200


# ── 이름을 링크로 만들지 말지 ──


def test_a_sentence_says_whether_its_author_is_gone(client, mine):
    def shown():
        items = client.get(f"/api/sentences/{mine['root']}/children").json()["items"]
        return next(item for item in items if item["id"] == mine["live"])

    assert shown()["author_withdrawn"] is False

    client.delete("/api/me")

    gone = shown()
    assert gone["author_withdrawn"] is True
    assert gone["author_nickname"] == "탈퇴한 작가"
