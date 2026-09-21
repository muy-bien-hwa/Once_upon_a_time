"""DB가 데이터 모델 규칙(docs 05-data-model)을 직접 지키는지 확인"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

INSERT_SENTENCE = text(
    "INSERT INTO sentences (story_id, author_id, content, depth, status) "
    "VALUES (:story, :author, :content, :depth, :status) RETURNING id"
)


def add_sentence(conn, seed, content="옛날 옛적에", depth=0, status="active"):
    params = {**seed, "content": content, "depth": depth, "status": status}
    return conn.execute(INSERT_SENTENCE, params).scalar_one()


def rejected_by(conn, sql, params):
    """SQL을 실행했을 때 DB가 거부하면, 거부한 제약조건 이름을 돌려줌"""
    with pytest.raises(IntegrityError) as exc:
        conn.execute(sql, params)
    return exc.value.orig.diag.constraint_name


def test_valid_first_sentence_is_saved(db_conn, seed):
    assert add_sentence(db_conn, seed) is not None


@pytest.mark.parametrize(
    ("content", "depth", "status", "constraint"),
    [
        ("   ", 0, "active", "ck_sentences_content_not_blank"),
        ("옛날 옛적에", 1, "active", "ck_sentences_root_iff_depth_zero"),
        ("옛날 옛적에", 0, "hidden", "ck_sentences_status_valid"),
    ],
    ids=["blank-content", "root-with-depth-1", "unknown-status"],
)
def test_invalid_sentence_is_rejected(db_conn, seed, content, depth, status, constraint):
    params = {**seed, "content": content, "depth": depth, "status": status}

    assert rejected_by(db_conn, INSERT_SENTENCE, params) == constraint


def test_story_has_only_one_first_sentence(db_conn, seed):
    # 스토리당 첫 문장은 1개 (D-65)
    add_sentence(db_conn, seed, content="첫 문장")
    params = {**seed, "content": "두 번째 첫 문장", "depth": 0, "status": "active"}

    assert rejected_by(db_conn, INSERT_SENTENCE, params) == "uq_sentences_one_root_per_story"


def test_first_sentence_cannot_be_deleted(db_conn, seed):
    # 첫 문장은 삭제 상태가 될 수 없음 (D-66)
    params = {**seed, "content": "첫 문장", "depth": 0, "status": "deleted"}

    assert rejected_by(db_conn, INSERT_SENTENCE, params) == "ck_sentences_root_not_deleted"


def test_report_needs_exactly_one_target(db_conn, seed):
    sql = text("INSERT INTO reports (reporter_id) VALUES (:voter)")

    assert rejected_by(db_conn, sql, seed) == "ck_reports_one_target"


def test_same_user_cannot_vote_twice(db_conn, seed):
    sentence_id = add_sentence(db_conn, seed)
    vote = text("INSERT INTO sentence_votes (user_id, sentence_id, value) VALUES (:u, :s, 1)")
    params = {"u": seed["voter"], "s": sentence_id}
    db_conn.execute(vote, params)

    assert rejected_by(db_conn, vote, params) == "pk_sentence_votes"
