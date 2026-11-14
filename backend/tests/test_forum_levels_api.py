"""커뮤니티 글·댓글 옆의 작성자 레벨 (D-100)

- 여기서 보이는 레벨은 작가 화면이 말하는 레벨과 **늘 같아야** 한다
- 작성자를 가린 줄(접힘)은 레벨도 가린다 — 레벨만 남으면 가린 사람이 누구인지 좁혀지므로
- 작성자가 몇 명이든 **쿼리 수가 늘지 않아야** 한다 (한 줄씩 물으면 글 수만큼 늘어남)
"""

from contextlib import contextmanager

import pytest
from sqlalchemy import event, text

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
    "VALUES (:story, :author, :title, '글 본문이다.') RETURNING id"
)
ADD_COMMENT = text(
    "INSERT INTO forum_comments (post_id, author_id, body) "
    "VALUES (:post, :author, :body) RETURNING id"
)
FOLD_POST = text("UPDATE forum_posts SET status = 'folded' WHERE id = :id")
FOLD_COMMENT = text("UPDATE forum_comments SET status = 'folded' WHERE id = :id")


@pytest.fixture
def story(client):
    """글을 쓸 스토리 하나 (로그인 유저가 시작 → 그 사람은 이미 문장 1개 = 「가」 단계)"""
    return client.post("/api/stories", json={"title": "제목", "content": "첫 문장이다."}).json()


@pytest.fixture
def make(client, db_conn, story):
    """이 파일에서 쓰는 손놀림 모음 — 사람 만들기 · 문장 보태기 · 글·댓글 쓰기"""
    story_id = story["story"]["id"]
    root = story["sentence"]["id"]

    def person(name: str, sentences: int = 0) -> int:
        user_id = db_conn.execute(ADD_USER, {"sub": f"sub-{name}", "nickname": name}).scalar_one()
        for number in range(sentences):
            db_conn.execute(
                ADD_SENTENCE,
                {
                    "story": story_id,
                    "parent": root,
                    "author": user_id,
                    "content": f"{name}의 {number + 1}번째 문장이다.",
                },
            )
        return user_id

    def post(author: int, title: str = "글 제목") -> int:
        return db_conn.execute(
            ADD_POST, {"story": story_id, "author": author, "title": title}
        ).scalar_one()

    def comment(post_id: int, author: int, body: str = "댓글이다.") -> int:
        return db_conn.execute(
            ADD_COMMENT, {"post": post_id, "author": author, "body": body}
        ).scalar_one()

    return {"story": story_id, "person": person, "post": post, "comment": comment}


def posts_of(client, story_id: int) -> list[dict]:
    return client.get(f"/api/stories/{story_id}/forum/posts").json()["items"]


def level_on_author_page(client, nickname: str) -> tuple:
    body = client.get(f"/api/users/{nickname}").json()
    return body["level_name"], body["level_label"]


def test_post_list_shows_the_same_level_as_the_author_page(client, make):
    """목록 옆의 레벨과 작가 화면의 레벨이 다르면, 둘 중 하나는 거짓말이 된다"""
    # 문장 3개 = 30점 = 3단계 「갸」
    writer = make["person"]("세문장", sentences=3)
    make["post"](writer)

    found = posts_of(client, make["story"])[0]

    assert found["author_level_name"] == "갸"
    assert found["author_level_label"] == "「갸」 단계"
    assert (found["author_level_name"], found["author_level_label"]) == level_on_author_page(
        client, "세문장"
    )


def test_comment_list_shows_the_same_level_as_the_author_page(client, make):
    writer = make["person"]("댓쓴이", sentences=2)
    post_id = make["post"](writer)
    make["comment"](post_id, writer)

    found = client.get(f"/api/forum/posts/{post_id}/comments").json()["items"][0]

    assert found["author_level_name"] == "개"  # 문장 2개 = 20점 = 2단계
    assert (found["author_level_name"], found["author_level_label"]) == level_on_author_page(
        client, "댓쓴이"
    )


def test_one_post_shows_it_too(client, make):
    """글 하나만 볼 때도 같은 길을 지나는지 (목록에만 붙고 상세에서 빠지면 화면이 깜빡임)"""
    writer = make["person"]("상세", sentences=1)
    post_id = make["post"](writer)

    found = client.get(f"/api/forum/posts/{post_id}").json()

    assert found["author_level_name"] == "가"


def test_a_folded_row_hides_the_level_as_well(client, db_conn, make):
    """작성자를 가린 줄에 레벨만 남으면, 레벨로 누구인지 좁힐 수 있다"""
    writer = make["person"]("가려질이", sentences=5)
    post_id = make["post"](writer)
    comment_id = make["comment"](post_id, writer)
    db_conn.execute(FOLD_POST, {"id": post_id})
    db_conn.execute(FOLD_COMMENT, {"id": comment_id})

    found = posts_of(client, make["story"])[0]
    said = client.get(f"/api/forum/posts/{post_id}/comments").json()["items"][0]

    assert found["author_nickname"] is None
    assert found["author_level_name"] is None
    assert said["author_nickname"] is None
    assert said["author_level_name"] is None


def test_someone_who_only_talks_has_no_level_yet(client, make):
    """커뮤니티에만 글을 쓰고 이야기에는 한 문장도 안 쓴 사람 → 0단계"""
    talker = make["person"]("말만", sentences=0)
    make["post"](talker)

    found = posts_of(client, make["story"])[0]

    assert found["author_level_name"] is None
    assert found["author_level_label"] == "아직 레벨이 없어요"


@contextmanager
def counting(db_conn):
    """이 블록 안에서 DB로 나간 질의를 모두 센다"""
    sent: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany):
        sent.append(statement)

    event.listen(db_conn.engine, "before_cursor_execute", record)
    try:
        yield sent
    finally:
        event.remove(db_conn.engine, "before_cursor_execute", record)


def test_more_authors_do_not_mean_more_queries(client, db_conn, make):
    """작성자가 늘어도 질의 수가 그대로여야 한다

    한 줄씩 레벨을 물으면 글 10개짜리 목록에서 질의가 10번 늘어난다.
    그 실수가 다시 들어와도 여기서 걸리도록, 작성자 1명일 때와 4명일 때를 **견주어** 센다
    (목록 자체가 쓰는 질의 수는 양쪽에서 똑같이 빠지므로 숫자를 외울 필요가 없다)
    """
    story_id = make["story"]
    make["post"](make["person"]("혼자", sentences=1), "첫 글")
    with counting(db_conn) as one_author:
        assert len(posts_of(client, story_id)) == 1

    for number in range(3):
        make["post"](make["person"](f"여럿{number}", sentences=number + 1), f"글 {number}")
    with counting(db_conn) as four_authors:
        assert len(posts_of(client, story_id)) == 4

    assert len(four_authors) == len(one_author)
