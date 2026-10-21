"""화면 내보내기 + 공유 미리보기 (D-81·F-05)

- /s/{문장번호}로 들어오면 그 문장 내용으로 공유 카드를 채움
- 가려진 문장(접힘·삭제)의 내용은 카드에도 쓰지 않음 (D-63·D-69)
"""

import pytest
from sqlalchemy import text

from app.web import INDEX, SHARE_END, SHARE_START, share_tags, tags_for, with_share_tags

PAGE = f"<head>{SHARE_START}<title>옛날 옛적에</title>{SHARE_END}</head><body></body>"


@pytest.fixture
def story(client):
    return client.post(
        "/api/stories", json={"title": "말하는 고양이", "content": "옛날 옛적에 고양이가 살았다."}
    ).json()


def test_sentence_card_shows_the_story_and_the_sentence(db_session, story):
    tags = tags_for(db_session, f"s/{story['sentence']['id']}")

    assert "말하는 고양이 · 옛날 옛적에" in tags
    assert "옛날 옛적에 고양이가 살았다." in tags
    assert f'og:url" content="http://localhost:8000/s/{story["sentence"]["id"]}"' in tags


@pytest.mark.parametrize("status", ["folded", "deleted"])
def test_hidden_sentence_is_not_shared(client, db_conn, db_session, story, status):
    # 첫 문장은 "삭제" 상태가 될 수 없어서(D-66) 이어 쓴 문장으로 확인
    sentence_id = client.post(
        f"/api/sentences/{story['sentence']['id']}/children", json={"content": "고양이가 말했다."}
    ).json()["id"]
    db_conn.execute(
        text("UPDATE sentences SET status = :status WHERE id = :id"),
        {"status": status, "id": sentence_id},
    )

    tags = tags_for(db_session, f"s/{sentence_id}")

    assert "고양이가 말했다" not in tags
    assert "지워졌거나 신고 처리된 문장이에요." in tags


def test_removed_sentence_falls_back_to_the_default_card(db_conn, db_session, story):
    sentence_id = story["sentence"]["id"]
    db_conn.execute(
        text("UPDATE sentences SET status = 'removed' WHERE id = :id"), {"id": sentence_id}
    )

    assert tags_for(db_session, f"s/{sentence_id}") is None


@pytest.mark.parametrize("path", ["", "stories/3/forum", "s/", "s/abc", "s/999999"])
def test_other_paths_keep_the_default_card(db_session, path):
    assert tags_for(db_session, path) is None


def test_quotes_in_a_title_cannot_break_the_tags():
    tags = share_tags('제목 "큰따옴표" <b>', "문장 & 기호", "http://localhost:8000/s/1")

    assert '"큰따옴표"' not in tags
    assert "<b>" not in tags
    assert "&amp;" in tags


def test_card_is_swapped_into_the_page():
    swapped = with_share_tags(PAGE, "<title>바뀐 제목</title>")

    assert swapped == "<head><title>바뀐 제목</title></head><body></body>"


def test_page_is_unchanged_without_a_card():
    assert with_share_tags(PAGE, None) == PAGE


@pytest.mark.skipif(not INDEX.exists(), reason="frontend/dist 빌드가 있어야 확인할 수 있음")
def test_built_page_is_served_with_the_card(client, story):
    """빌드가 있을 때만: 주소로 들어오면 화면 파일 + 그 문장의 공유 카드"""
    page = client.get(f"/s/{story['sentence']['id']}")

    assert page.status_code == 200
    assert "말하는 고양이" in page.text
    assert '<div id="root">' in page.text


@pytest.mark.skipif(not INDEX.exists(), reason="frontend/dist 빌드가 있어야 확인할 수 있음")
def test_unknown_api_address_is_still_json(client):
    """화면 파일이 API 주소를 가로채지 않는지"""
    response = client.get("/api/없는주소")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "NOT_FOUND"
