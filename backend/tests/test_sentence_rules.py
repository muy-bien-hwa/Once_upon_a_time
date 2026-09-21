"""문장 목록 공통 규칙 (services/sentences.py, docs 07 "문장 status별 응답"·"정렬")"""

from sqlalchemy import text

from app.models import Sentence
from app.services.sentences import fetch_sentences, order_sentences

ADD_SENTENCE = text(
    "INSERT INTO sentences (story_id, parent_id, author_id, content, depth, status) "
    "VALUES (:story, :parent, :author, :content, :depth, :status) RETURNING id"
)
ADD_USER = text(
    "INSERT INTO users (provider, provider_user_id, nickname) "
    "VALUES ('google', :sub, :sub) RETURNING id"
)
ADD_VOTE = text("INSERT INTO sentence_votes (user_id, sentence_id, value) VALUES (:u, :s, :v)")


def add(db_conn, seed, content, parent=None, status="active"):
    params = {
        "story": seed["story"],
        "parent": parent,
        "author": seed["author"],
        "content": content,
        "depth": 0 if parent is None else 1,
        "status": status,
    }
    return db_conn.execute(ADD_SENTENCE, params).scalar_one()


def children(db_session, parent_id, sort):
    items = fetch_sentences(db_session, Sentence.parent_id == parent_id)
    return order_sentences(items, sort, user_id=None)


def test_children_follow_status_rules(db_conn, db_session, seed):
    root = add(db_conn, seed, "첫 문장")
    for content, status in [
        ("먼저 쓴 문장", "active"),
        ("나중에 쓴 문장", "active"),
        ("접힌 문장", "folded"),
        ("지운 문장", "deleted"),
        ("숨긴 문장", "removed"),
    ]:
        add(db_conn, seed, content, root, status)

    items = children(db_session, root, "latest")

    # 숨김은 빠지고, 접힘·삭제는 맨 아래 / 보통 문장은 최근 것이 위
    assert [i.status for i in items] == ["active", "active", "folded", "deleted"]
    assert [i.content for i in items[:2]] == ["나중에 쓴 문장", "먼저 쓴 문장"]
    # 접힌 문장·삭제된 문장은 내용과 작성자를 보내지 않음 (D-63·D-69)
    for hidden in items[2:]:
        assert hidden.content is None
        assert hidden.author_nickname is None


def test_child_count_ignores_removed(db_conn, db_session, seed):
    root = add(db_conn, seed, "첫 문장")
    add(db_conn, seed, "보이는 문장", root)
    add(db_conn, seed, "숨긴 문장", root, "removed")

    [first] = fetch_sentences(db_session, Sentence.id == root)

    assert first.child_count == 1


def test_votes_sort_uses_up_minus_down(db_conn, db_session, seed):
    root = add(db_conn, seed, "첫 문장")
    liked = add(db_conn, seed, "추천 1 · 비추천 0", root)
    mixed = add(db_conn, seed, "추천 1 · 비추천 1", root)
    fans = [db_conn.execute(ADD_USER, {"sub": f"fan-{n}"}).scalar_one() for n in range(2)]
    db_conn.execute(ADD_VOTE, {"u": fans[0], "s": liked, "v": 1})
    db_conn.execute(ADD_VOTE, {"u": fans[0], "s": mixed, "v": 1})
    db_conn.execute(ADD_VOTE, {"u": fans[1], "s": mixed, "v": -1})

    by_votes = children(db_session, root, "votes")
    by_latest = children(db_session, root, "latest")

    # 추천순 = 추천 − 비추천 (D-64): 1 > 0 / 날짜순은 나중에 쓴 mixed가 위
    assert [i.id for i in by_votes] == [liked, mixed]
    assert [i.id for i in by_latest] == [mixed, liked]
    assert (by_votes[1].up_count, by_votes[1].down_count) == (1, 1)
