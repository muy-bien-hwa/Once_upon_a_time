"""신고 처리 표시와 정리 (운영정책 7조)

- 되돌려도 신고를 지우지 않고 "처리됨"으로 표시 → 왜 그런 조치를 했는지 나중에 설명할 수 있음
- 처리됨으로 표시한 신고는 다시 접는 셈에서 빠짐 (옛 신고로 또 접히지 않게)
- 처리한 지 3개월이 지나면 지움 (사본 없음)
"""

from datetime import UTC, datetime, timedelta
from itertools import count

import pytest
from sqlalchemy import text

from app.models import Report
from app.services.reports import mark_handled, purge_handled

ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :nickname) RETURNING id"
)
ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth) "
    "VALUES (:story, :parent, :author, '남이 쓴 문장이다.', 1) RETURNING id"
)
ADD_REPORT = text(
    "INSERT INTO reports (reporter_id, sentence_id, reason, resolved_at) "
    "VALUES (:user, :target, 'abuse', :resolved)"
)
ABUSE = {"reason": "abuse", "detail": "욕을 했어요"}

# 신고자 이름이 겹치지 않게 (한 테스트에서 여러 번 쌓음)
numbering = count()


@pytest.fixture
def now():
    return datetime.now(UTC)


@pytest.fixture
def sentence_id(client, db_conn, seed):
    """남이 이어 쓴 문장 (내가 신고할 수 있는 대상)"""
    story = client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()
    return db_conn.execute(
        ADD_SENTENCE,
        {
            "story": story["story"]["id"],
            "parent": story["sentence"]["id"],
            "author": seed["voter"],
        },
    ).scalar_one()


def pile_up(db_conn, target_id: int, count: int, resolved=None) -> None:
    """다른 사람들이 먼저 신고해 둔 상태를 만듦 (resolved를 주면 처리된 신고)"""
    for _ in range(count):
        number = next(numbering)
        reporter = db_conn.execute(
            ADD_USER, {"sub": f"reporter-{number}", "nickname": f"신고자{number}"}
        ).scalar_one()
        db_conn.execute(ADD_REPORT, {"user": reporter, "target": target_id, "resolved": resolved})


def status_of(db_conn, sentence_id: int) -> str:
    return db_conn.execute(
        text("SELECT status FROM sentences WHERE id = :id"), {"id": sentence_id}
    ).scalar_one()


def test_handled_reports_do_not_count_toward_folding(client, db_conn, sentence_id, now):
    """되돌린 글이 옛 신고 4건 때문에 내 신고 하나로 바로 다시 접히면 안 됨"""
    pile_up(db_conn, sentence_id, 4, resolved=now)

    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert status_of(db_conn, sentence_id) == "active"


def test_fresh_reports_still_fold_it_again(client, db_conn, sentence_id, now):
    """처리된 것과 별개로, 새 신고가 5건 모이면 다시 접힘"""
    pile_up(db_conn, sentence_id, 3, resolved=now)
    pile_up(db_conn, sentence_id, 4)

    client.post(f"/api/sentences/{sentence_id}/reports", json=ABUSE)

    assert status_of(db_conn, sentence_id) == "folded"


def test_marking_keeps_the_reports(db_session, db_conn, sentence_id):
    pile_up(db_conn, sentence_id, 3)

    assert mark_handled(db_session, Report.sentence_id, sentence_id) == 3

    stamped = db_conn.execute(
        text("SELECT count(*) FROM reports WHERE sentence_id = :id AND resolved_at IS NOT NULL"),
        {"id": sentence_id},
    ).scalar_one()
    assert stamped == 3


def test_marking_again_leaves_the_first_time_alone(db_session, db_conn, sentence_id, now):
    """이미 처리한 신고의 날짜를 덮어쓰면 3개월 세는 기준이 밀림"""
    pile_up(db_conn, sentence_id, 2, resolved=now - timedelta(days=30))

    assert mark_handled(db_session, Report.sentence_id, sentence_id) == 0


def test_purge_only_removes_old_handled_reports(db_session, db_conn, sentence_id, now):
    pile_up(db_conn, sentence_id, 2, resolved=now - timedelta(days=100))
    pile_up(db_conn, sentence_id, 1, resolved=now)
    pile_up(db_conn, sentence_id, 3)

    assert purge_handled(db_session) == 2

    left = db_conn.execute(
        text("SELECT count(*) FROM reports WHERE sentence_id = :id"), {"id": sentence_id}
    ).scalar_one()
    assert left == 4
