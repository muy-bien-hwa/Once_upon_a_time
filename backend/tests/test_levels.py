"""레벨 규칙 (D-100)

계획서에 적어 PM이 고른 숫자가 그대로 나오는지 확인한다.
"""

import pytest

from app.services import levels


def test_score_counts_sentences_ten_times_heavier():
    assert levels.score(sentence_count=3, received_up_count=5) == 35


def test_no_level_until_the_first_sentence():
    assert levels.level_of(0) == 0
    assert levels.level_of(9) == 0
    assert levels.name_of(0) is None
    assert levels.label_of(0) == "아직 레벨이 없어요"


def test_the_first_sentence_makes_level_one():
    assert levels.level_of(levels.score(1, 0)) == 1
    assert levels.name_of(1) == "가"
    assert levels.label_of(1) == "「가」 단계"


@pytest.mark.parametrize(
    ("level", "name"),
    [
        (1, "가"),
        (2, "개"),
        (21, "기"),  # 첫 줄 끝
        (22, "까"),  # 쌍자음 줄로 (PM 결정 A-가)
        (43, "나"),  # 셋째 줄 첫 글자
        (399, "히"),  # 마지막
    ],
)
def test_names_follow_the_dictionary_order(level, name):
    assert levels.name_of(level) == name


def test_every_level_has_its_own_name():
    names = {levels.name_of(n) for n in range(1, levels.MAX_LEVEL + 1)}
    assert len(names) == levels.MAX_LEVEL == 399


@pytest.mark.parametrize(
    ("level", "sentences"),
    [
        (21, 21),  # 「기」 — 1줄 끝
        (42, 63),  # 「끼」 — 2줄 끝
        (63, 126),  # 「니」 — 3줄 끝
        (399, 3990),  # 「히」 — 끝까지
    ],
)
def test_rows_get_heavier_as_you_climb(level, sentences):
    """계획서에 적은 "문장 몇 개면 어디까지" 숫자 그대로여야 한다"""
    assert levels.score_for(level) == sentences * levels.SENTENCE_POINTS
    assert levels.level_of(levels.score(sentences, 0)) == level


def test_one_point_short_stays_on_the_level_below():
    for level in (2, 22, 43, 399):
        assert levels.level_of(levels.score_for(level) - 1) == level - 1
        assert levels.level_of(levels.score_for(level)) == level


def test_level_and_score_agree_all_the_way_up():
    for level in range(1, levels.MAX_LEVEL + 1):
        assert levels.level_of(levels.score_for(level)) == level


def test_the_top_does_not_overflow():
    top = levels.score_for(levels.MAX_LEVEL)
    assert top == 39_900
    assert levels.level_of(top * 10) == levels.MAX_LEVEL
    assert levels.next_score(levels.MAX_LEVEL) is None


def test_standing_is_what_the_screen_needs():
    # 문장 27개(270점) + 추천 63개(63점) = 333점
    # → 첫 줄 210점을 다 쓰고(21단계), 남은 123점을 둘째 줄 20점씩 여섯 칸 = 27단계
    assert levels.standing(sentence_count=27, received_up_count=63) == {
        "score": 333,
        "level": 27,
        "level_name": "께",
        "level_label": "「께」 단계",
        # 27단계는 330점부터 (첫 줄 210점 + 둘째 줄 20점 × 6칸)
        "level_score": 330,
        "next_score": 350,
    }
