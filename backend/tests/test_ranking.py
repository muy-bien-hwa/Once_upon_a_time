"""문장 추천 정렬 점수 (docs 04-ranking-score)"""

from app.services.ranking import rank_score


def score(up, down, age_hours, j0=0.0, user_id=1, kst_date="2026-09-21"):
    return rank_score(
        up=up,
        down=down,
        age_hours=age_hours,
        user_id=user_id,
        sentence_id=1,
        kst_date=kst_date,
        b=1.0,
        h=48,
        j0=j0,
    )


def test_examples_in_design_doc():
    # docs 04 예시 표 (흔들기 제외)
    assert round(score(9, 0, 72), 2) == 1.35
    assert round(score(2, 0, 24), 2) == 1.18
    assert round(score(0, 0, 0), 2) == 1.00


def test_downvotes_lower_the_score():
    assert score(0, 9, 0) < score(0, 0, 0) < score(9, 0, 0)


def test_new_sentence_bonus_halves_every_48_hours():
    assert round(score(0, 0, 48), 3) == 0.5


def test_jitter_is_same_for_same_day_and_small():
    first = score(0, 0, 0, j0=0.3)
    again = score(0, 0, 0, j0=0.3)

    assert first == again
    assert abs(first - score(0, 0, 0)) <= 0.3
