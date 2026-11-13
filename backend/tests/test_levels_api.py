"""레벨·점수 내역·레벨 분포 API (D-100)

- 레벨은 내려가지 않고, 내가 보는 레벨과 남이 보는 레벨이 같다
- 점수 내역을 다 더하면 점수가 된다 (두 기능이 어긋나지 않는지 보는 확인)
- 레벨 분포는 로그인 없이 누구나 보고, 레벨이 없는 사람·탈퇴한 사람은 세지 않는다
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text

from app.services import levels

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status, created_at) "
    "VALUES (:story, :parent, :author, :content, :depth, :status, :at) RETURNING id"
)
ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :nickname) RETURNING id"
)
ADD_VOTE = text(
    "INSERT INTO sentence_votes (user_id, sentence_id, value, created_at) "
    "VALUES (:user, :sentence, :value, :at)"
)
SET_TIME = text("UPDATE sentences SET created_at = :at WHERE id = :id")
WITHDRAW = text("UPDATE users SET nickname = NULL, deleted_at = now() WHERE id = :id")


def day(number: int) -> datetime:
    """시각을 눈에 보이게 정함 — 한 트랜잭션 안에서는 now()가 전부 같은 값이라 순서가 생기지 않는다"""
    return datetime(2026, 11, number, 12, 0, tzinfo=UTC)


@pytest.fixture
def wrote(client, db_conn, seed):
    """두 스토리에 걸쳐 쓴 내 문장 여섯 + 받은 추천 셋 (비추천 하나는 점수에 들어가지 않음)"""

    def open_story(title: str, content: str, number: int) -> tuple[int, int]:
        story = client.post("/api/stories", json={"title": title, "content": content}).json()
        root = story["sentence"]["id"]
        db_conn.execute(SET_TIME, {"at": day(number), "id": root})
        return story["story"]["id"], root

    def add(story, parent, number, content, status="active", author=None, depth=1) -> int:
        return db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story,
                "parent": parent,
                "author": author or seed["author"],
                "content": content,
                "depth": depth,
                "status": status,
                "at": day(number),
            },
        ).scalar_one()

    def vote(sentence: int, number: int, value: int = 1) -> None:
        fan = db_conn.execute(
            ADD_USER, {"sub": f"fan-{number}", "nickname": f"팬{number}"}
        ).scalar_one()
        db_conn.execute(
            ADD_VOTE, {"user": fan, "sentence": sentence, "value": value, "at": day(number)}
        )

    lighthouse, first = open_story("등대가 꺼진 밤", "등대가 꺼졌다.", 1)
    forest, start = open_story("숲으로 간 우체부", "우체부가 숲에 들어섰다.", 2)
    mine = {
        "lighthouse": lighthouse,
        "forest": forest,
        "first": first,
        "start": start,
        "second": add(lighthouse, first, 3, "등대지기는 노랫소리를 들었다."),
        "folded": add(lighthouse, first, 4, "접힌 문장이다.", "folded"),
        "deleted": add(lighthouse, first, 5, "지운 문장이다.", "deleted"),
        "third": add(forest, start, 6, "우체부는 편지를 묻었다."),
    }
    vote(mine["second"], 7)
    vote(mine["second"], 8)
    vote(mine["first"], 9)
    # 비추천은 점수를 깎지 않으므로 내역에도 없어야 함 (가장 최근 일이라 섞이면 바로 보인다)
    vote(mine["third"], 10, value=-1)
    return mine


# 문장 여섯 × 10점 + 추천 셋 × 1점
SCORE = 63
EVENTS = 9


def standing() -> dict:
    return levels.standing(sentence_count=6, received_up_count=3)


def history(client, query: str = "size=50") -> dict:
    return client.get(f"/api/me/score-history?{query}").json()


def marks(page: dict) -> list[tuple]:
    """한 쪽에 담긴 일들 — 순서까지 그대로 비교하려고"""
    return [(item["kind"], item["sentence_id"], item["at"]) for item in page["items"]]


# ── 마이페이지·작가 화면의 레벨 ──


def test_my_summary_carries_my_level(client, wrote):
    summary = client.get("/api/me/summary").json()

    assert summary["sentence_count"] == 6
    assert summary["received_up_count"] == 3
    assert summary["score"] == SCORE
    assert {key: summary[key] for key in standing()} == standing()


def test_an_author_page_shows_the_same_level_as_my_own_page(client, wrote):
    mine = client.get("/api/me/summary").json()
    author = client.get("/api/users/author").json()

    assert {key: author[key] for key in standing()} == {key: mine[key] for key in standing()}
    # 보이는 문장만 센 숫자(여섯 중 넷)와 점수는 일부러 어긋남
    assert author["sentence_count"] == 4


def test_a_writer_with_nothing_has_no_level(client, seed):
    summary = client.get("/api/me/summary").json()

    assert summary["score"] == 0
    assert summary["level"] == 0
    assert summary["level_name"] is None
    assert summary["level_label"] == "아직 레벨이 없어요"


@pytest.fixture
def chain(client, db_conn, seed):
    """내 문장 뒤에 남이 이어 쓴 상태 — 내가 지우면 자리만 남는다(deleted)"""
    story = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    root = story["sentence"]["id"]

    def add(parent: int, author: int, content: str, depth: int, number: int) -> int:
        return db_conn.execute(
            ADD_SENTENCE,
            {
                "story": story["story"]["id"],
                "parent": parent,
                "author": author,
                "content": content,
                "depth": depth,
                "status": "active",
                "at": day(number),
            },
        ).scalar_one()

    mine = add(root, seed["author"], "내가 쓴 문장이다.", 1, 1)
    add(mine, seed["voter"], "남이 이어 쓴 문장이다.", 2, 2)
    return {"root": root, "mine": mine}


def test_deleting_my_sentence_does_not_lower_my_level(client, chain):
    before = client.get("/api/me/summary").json()
    before_author = client.get("/api/users/author").json()

    deleted = client.delete(f"/api/sentences/{chain['mine']}").json()

    assert deleted == {"status": "deleted"}
    after = client.get("/api/me/summary").json()
    after_author = client.get("/api/users/author").json()
    assert (after["score"], after["level"]) == (before["score"], before["level"])
    # 남이 보는 레벨도 그대로 — 줄어드는 것은 "보이는 문장 수"뿐
    assert (after_author["score"], after_author["level"]) == (before["score"], before["level"])
    assert after_author["sentence_count"] == before_author["sentence_count"] - 1


# ── 점수 내역 ──


def test_score_history_adds_up_to_my_score(client, wrote):
    score = client.get("/api/me/summary").json()["score"]
    listing = history(client)

    assert listing["total"] == EVENTS
    assert sum(item["points"] for item in listing["items"]) == score == SCORE
    kinds = [item["kind"] for item in listing["items"]]
    assert (kinds.count("sentence"), kinds.count("up")) == (6, 3)
    # 스토리가 둘이어도 한 목록에 함께 나옴
    assert {item["story_title"] for item in listing["items"]} == {
        "등대가 꺼진 밤",
        "숲으로 간 우체부",
    }


def test_score_history_is_newest_first(client, wrote):
    times = [item["at"] for item in history(client)["items"]]

    assert times == sorted(times, reverse=True)
    assert datetime.fromisoformat(times[0]) == day(9)


def test_score_history_keeps_hidden_text_to_itself(client, wrote):
    written = {
        item["sentence_id"]: item for item in history(client)["items"] if item["kind"] == "sentence"
    }

    assert written[wrote["second"]]["sentence_content"] == "등대지기는 노랫소리를 들었다."
    assert written[wrote["deleted"]]["sentence_content"] is None
    assert written[wrote["folded"]]["sentence_content"] is None


def test_score_history_leaves_out_down_votes(client, wrote):
    ups = [item for item in history(client)["items"] if item["kind"] == "up"]

    assert [item["sentence_id"] for item in ups] == [
        wrote["first"],
        wrote["second"],
        wrote["second"],
    ]
    assert all(item["points"] == 1 for item in ups)


def test_score_history_comes_in_pages(client, wrote):
    whole = history(client)
    page_one = history(client, "page=1&size=4")
    page_two = history(client, "page=2&size=4")

    assert page_one["total"] == page_two["total"] == EVENTS
    assert (page_two["page"], page_two["size"]) == (2, 4)
    # 쪽을 넘기면 앞 쪽이 끝난 자리에서 이어짐 (빠지거나 겹치지 않음)
    assert marks(page_one) == marks(whole)[:4]
    assert marks(page_two) == marks(whole)[4:8]


def test_score_history_does_not_lose_an_event_when_times_tie(client, db_conn, wrote):
    """같은 시각에 들어온 추천이 섞여도 쪽을 넘기며 하나씩 다 보인다 (겹치거나 빠지지 않음)"""
    for number, sentence in ((20, wrote["second"]), (21, wrote["third"])):
        fan = db_conn.execute(
            ADD_USER, {"sub": f"tie-{number}", "nickname": f"동시{number}"}
        ).scalar_one()
        db_conn.execute(ADD_VOTE, {"user": fan, "sentence": sentence, "value": 1, "at": day(9)})

    whole = history(client)
    one_by_one = [
        marks(history(client, f"page={page}&size=1"))[0] for page in range(1, whole["total"] + 1)
    ]

    assert whole["total"] == EVENTS + 2
    assert one_by_one == marks(whole)
    assert len(set(one_by_one)) == whole["total"]


def test_score_history_needs_login(client):
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    client.cookies.clear()

    assert client.get("/api/me/score-history").status_code == 401


# ── 레벨 분포 ──


@pytest.fixture
def writers(client, db_conn, seed, wrote):
    """다른 작가 둘: 문장 하나뿐인 사람과, 썼지만 탈퇴한 사람"""

    def writer(sub: str, nickname: str, content: str, number: int) -> int:
        user = db_conn.execute(ADD_USER, {"sub": sub, "nickname": nickname}).scalar_one()
        db_conn.execute(
            ADD_SENTENCE,
            {
                "story": wrote["lighthouse"],
                "parent": wrote["first"],
                "author": user,
                "content": content,
                "depth": 1,
                "status": "active",
                "at": day(number),
            },
        )
        return user

    writer("rookie-sub", "신입", "불빛이 다시 켜졌다.", 11)
    gone = writer("gone-sub", "떠난사람", "그리고 아무도 없었다.", 12)
    db_conn.execute(WITHDRAW, {"id": gone})
    return {"gone": gone}


def test_distribution_counts_each_level(client, wrote, writers):
    body = client.get("/api/levels/distribution").json()
    author_level = client.get("/api/users/author").json()["level"]

    assert {item["level"]: item["count"] for item in body["items"]} == {1: 1, author_level: 1}
    # 문장 하나면 10점 → 1단계 「가」
    assert body["items"][0] == {"level": 1, "name": "가", "count": 1}
    # 추천만 누른 사람(문장이 없어 레벨도 없음)과 탈퇴한 사람은 세지 않음
    assert body["total_writers"] == 2


def test_distribution_is_sorted_from_the_bottom(client, wrote, writers):
    shown = [item["level"] for item in client.get("/api/levels/distribution").json()["items"]]

    assert shown == sorted(shown)


def test_distribution_works_without_logging_in(client, wrote, writers):
    from app.deps import get_current_user, get_optional_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_optional_user)
    client.cookies.clear()

    response = client.get("/api/levels/distribution")

    assert response.status_code == 200
    assert response.json()["total_writers"] == 2
