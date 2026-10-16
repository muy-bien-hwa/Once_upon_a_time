"""신고·자동 접기 (F-10, D-13·D-49·D-82·D-93)

- 1인 1회 · 자기 글은 불가 · 내용이 가려진 대상은 불가
- 사유 7종 + 설명 500자 ("기타"는 설명 필수)
- 5건 쌓이면 같은 처리 안에서 접힘(folded) → 문장·커뮤니티 글·댓글 공통
"""

from typing import get_args

import pytest
from sqlalchemy import text

ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :nickname) RETURNING id"
)
ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, :content, 1) RETURNING id"
)
ADD_POST = text(
    "INSERT INTO forum_posts (story_id, author_id, title, body) "
    "VALUES (:story, :author, '남이 쓴 글', '본문') RETURNING id"
)
ADD_COMMENT = text(
    "INSERT INTO forum_comments (post_id, author_id, body) "
    "VALUES (:post, :author, '남이 쓴 댓글') RETURNING id"
)
ABUSE = {"reason": "abuse", "detail": "욕을 했어요"}


def pile_up(db_conn, column: str, target_id: int, count: int) -> None:
    """다른 사람들이 먼저 신고해 둔 상태를 만듦 (column = sentence_id·post_id·comment_id)"""
    add_report = text(
        f"INSERT INTO reports (reporter_id, {column}, reason) VALUES (:user, :target, 'abuse')"
    )
    for number in range(count):
        reporter = db_conn.execute(
            ADD_USER, {"sub": f"{column}-{number}", "nickname": f"신고자{number}"}
        ).scalar_one()
        db_conn.execute(add_report, {"user": reporter, "target": target_id})


@pytest.fixture
def story(client):
    """내가 시작한 스토리 (첫 문장도 내 것)"""
    return client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()


@pytest.fixture
def sentence_id(db_conn, story, seed):
    """남이 이어 쓴 문장 (내가 신고할 수 있는 대상)"""
    return db_conn.execute(
        ADD_SENTENCE,
        {
            "story": story["story"]["id"],
            "parent": story["sentence"]["id"],
            "author": seed["voter"],
            "content": "남이 쓴 문장이다.",
        },
    ).scalar_one()


@pytest.fixture
def post_id(db_conn, story, seed):
    """남이 쓴 커뮤니티 글"""
    return db_conn.execute(
        ADD_POST, {"story": story["story"]["id"], "author": seed["voter"]}
    ).scalar_one()


@pytest.fixture
def comment_id(db_conn, post_id, seed):
    """남이 쓴 댓글"""
    return db_conn.execute(ADD_COMMENT, {"post": post_id, "author": seed["voter"]}).scalar_one()


def children_of(client, parent_id: int) -> list[dict]:
    return client.get(f"/api/sentences/{parent_id}/children").json()["items"]


def test_report_is_saved_with_the_reason_and_detail(client, db_conn, sentence_id):
    response = client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert response.status_code == 201
    # 신고 수는 아무에게도 보여주지 않음 → 접수됐다는 사실만 (D-93)
    assert response.json() == {"reported": True}
    saved = db_conn.execute(
        text("SELECT reason, detail FROM reports WHERE sentence_id = :id"), {"id": sentence_id}
    ).one()
    assert saved == ("abuse", "욕을 했어요")


def test_my_report_shows_on_the_sentence(client, story, sentence_id):
    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    shown = children_of(client, story["sentence"]["id"])[0]
    # 버튼이 "신고했어요"로 바뀌도록 내 신고 여부만 보냄 (신고 수는 없음, D-93)
    assert shown["reported_by_me"] is True
    assert "report_count" not in shown


def test_detail_is_optional_except_for_other(client, sentence_id):
    response = client.post(f"/api/sentences/{sentence_id}/reports", json={"reason": "spam"})

    assert response.status_code == 201


def test_other_reason_needs_a_detail(client, sentence_id):
    response = client.post(f"/api/sentences/{sentence_id}/reports", json={"reason": "other"})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "REPORT_DETAIL_REQUIRED"
    with_detail = client.post(
        f"/api/sentences/{sentence_id}/reports", json={"reason": "other", "detail": "이상해요"}
    )
    assert with_detail.status_code == 201


def test_detail_over_500_characters_is_refused(client, sentence_id):
    body = {"reason": "abuse", "detail": "가" * 501}

    assert client.post(f"/api/sentences/{sentence_id}/reports", json=body).status_code == 422


def test_unknown_reason_is_refused(client, sentence_id):
    body = {"reason": "그냥", "detail": ""}

    assert client.post(f"/api/sentences/{sentence_id}/reports", json=body).status_code == 422


def test_reporting_twice_is_refused(client, sentence_id):
    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    response = client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ALREADY_REPORTED"


def test_cannot_report_my_own_sentence(client, story):
    response = client.post(f"/api/sentences/{story['sentence']['id']}/reports", json=ABUSE)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SELF_REPORT"


def test_five_reports_fold_the_sentence(client, db_conn, story, sentence_id):
    pile_up(db_conn, "sentence_id", sentence_id, 4)

    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    shown = children_of(client, story["sentence"]["id"])[0]
    # 접히면 내용과 작성자가 가려짐 → 화면엔 "신고 처리된 문장입니다."만 (D-69)
    assert (shown["status"], shown["content"], shown["author_nickname"]) == ("folded", None, None)


def test_four_reports_leave_the_sentence_alone(client, db_conn, story, sentence_id):
    pile_up(db_conn, "sentence_id", sentence_id, 3)

    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert children_of(client, story["sentence"]["id"])[0]["status"] == "active"


def test_folded_sentence_blocks_writing_after_it(client, db_conn, sentence_id):
    """접히면 그 뒤에는 이어 쓸 수 없음 (D-70)"""
    pile_up(db_conn, "sentence_id", sentence_id, 4)
    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    response = client.post(f"/api/sentences/{sentence_id}/children", json={"content": "이어 쓴다."})

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PARENT_FOLDED"


@pytest.mark.parametrize("status", ["folded", "deleted"])
def test_cannot_report_a_hidden_sentence(client, db_conn, sentence_id, status):
    """이미 가려진 내용에는 신고도 하지 않음 (투표와 같은 이유, D-82)"""
    db_conn.execute(
        text("UPDATE sentences SET status = :status WHERE id = :id"),
        {"status": status, "id": sentence_id},
    )

    response = client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "REPORT_NOT_ALLOWED"


def test_missing_sentence_is_not_found(client):
    assert client.post("/api/sentences/999999/reports", json=ABUSE).status_code == 404


def test_report_needs_login(client, sentence_id, monkeypatch):
    from app.config import settings
    from app.deps import get_current_user
    from app.main import app

    app.dependency_overrides.pop(get_current_user)
    monkeypatch.setattr(settings, "dev_user_id", None)
    client.cookies.clear()

    assert client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE).status_code == 401


def test_five_reports_fold_the_post(client, db_conn, post_id):
    pile_up(db_conn, "post_id", post_id, 4)

    assert client.post(f"/api/forum/posts/{post_id}/reports", json=ABUSE).status_code == 201

    shown = client.get(f"/api/forum/posts/{post_id}").json()
    # 접힌 글은 제목·본문·작성자가 가려짐
    assert (shown["status"], shown["title"], shown["body"]) == ("folded", None, None)
    assert "report_count" not in shown


def test_my_report_shows_on_the_post(client, post_id):
    client.post(f"/api/forum/posts/{post_id}/reports", json=ABUSE)

    assert client.get(f"/api/forum/posts/{post_id}").json()["reported_by_me"] is True


def test_cannot_report_my_own_post(client, story):
    mine = client.post(
        f"/api/stories/{story['story']['id']}/forum/posts",
        json={"title": "내 글", "body": "본문"},
    ).json()

    response = client.post(f"/api/forum/posts/{mine['id']}/reports", json=ABUSE)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "SELF_REPORT"


def test_deleted_post_cannot_be_reported(client, db_conn, post_id):
    db_conn.execute(
        text("UPDATE forum_posts SET status = 'removed' WHERE id = :id"), {"id": post_id}
    )

    response = client.post(f"/api/forum/posts/{post_id}/reports", json=ABUSE)

    assert response.status_code == 404
    assert response.json()["detail"]["message"] == "삭제된 글입니다"


def test_five_reports_fold_the_comment(client, db_conn, post_id, comment_id):
    pile_up(db_conn, "comment_id", comment_id, 4)

    assert client.post(f"/api/forum/comments/{comment_id}/reports", json=ABUSE).status_code == 201

    shown = client.get(f"/api/forum/posts/{post_id}/comments").json()["items"][0]
    assert (shown["status"], shown["body"], shown["author_nickname"]) == ("folded", None, None)
    assert "report_count" not in shown


def test_my_report_shows_on_the_comment(client, post_id, comment_id):
    client.post(f"/api/forum/comments/{comment_id}/reports", json=ABUSE)

    shown = client.get(f"/api/forum/posts/{post_id}/comments").json()["items"][0]
    assert shown["reported_by_me"] is True


def test_folded_comment_cannot_get_replies(client, db_conn, post_id, comment_id):
    pile_up(db_conn, "comment_id", comment_id, 4)
    client.post(f"/api/forum/comments/{comment_id}/reports", json=ABUSE)

    response = client.post(
        f"/api/forum/posts/{post_id}/comments", json={"body": "답글", "parent_id": comment_id}
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "COMMENT_NOT_ALLOWED"


def test_comment_in_a_deleted_post_cannot_be_reported(client, db_conn, post_id, comment_id):
    db_conn.execute(
        text("UPDATE forum_posts SET status = 'removed' WHERE id = :id"), {"id": post_id}
    )

    assert client.post(f"/api/forum/comments/{comment_id}/reports", json=ABUSE).status_code == 404


def test_reasons_in_the_api_and_the_table_match():
    """화면에서 고를 수 있는 사유와 DB가 받아 주는 사유가 어긋나지 않게 (D-93)"""
    from app.models.report import REASONS
    from app.schemas.report import ReportReason

    assert set(get_args(ReportReason)) == set(REASONS)
