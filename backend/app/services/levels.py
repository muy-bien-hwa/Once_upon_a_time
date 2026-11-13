"""레벨 (D-100)

점수 = 쓴 문장 × 10 + 받은 추천 × 1
이름 = 「가」부터 「히」까지 399단계 — 받침 없는 한글 음절을 사전 순서로
속도 = n번째 자음 줄에서는 한 글자 오르는 데 10n점 (가 줄 10점 · 까 줄 20점 … 하 줄 190점)

저장하는 것이 하나도 없다. 늘 지금 숫자에서 계산한다 →
나중에 아래 숫자만 바꾸면 지난 기록까지 전부 새 기준으로 맞춰진다.
"""

# 점수 (D-100)
SENTENCE_POINTS = 10
UP_POINTS = 1

# 이름 (유니코드 한글은 "초성 × 21모음 × 28받침" 순서로 놓여 있다.
# 받침을 0으로 두고 28칸씩 건너뛰면 받침 없는 음절이 사전 순서로 나온다)
FIRST_SYLLABLE = 0xAC00
FINALS = 28
VOWELS = 21
CONSONANTS = 19
MAX_LEVEL = CONSONANTS * VOWELS  # 399 — 「히」

# 첫 줄(가~기)에서 한 글자의 값. 줄이 올라갈수록 이 값의 배수로 무거워진다
ROW_POINTS = 10


def score(sentence_count: int, received_up_count: int) -> int:
    """지금 점수. 문장은 지운 것·접힌 것까지 세고(내려가지 않게), 추천은 지금 받고 있는 수"""
    return sentence_count * SENTENCE_POINTS + received_up_count * UP_POINTS


def level_of(points: int) -> int:
    """점수로 몇 단계인지. 아직 한 문장도 없으면 0 (= 레벨 없음)"""
    level = 0
    left = points
    for row in range(1, CONSONANTS + 1):
        step = ROW_POINTS * row
        whole_row = VOWELS * step
        if left >= whole_row:
            level += VOWELS
            left -= whole_row
        else:
            return level + left // step
    return MAX_LEVEL  # 끝까지 올라간 사람


def score_for(level: int) -> int:
    """그 단계가 되는 데 필요한 점수 (0단계는 0점)"""
    if level <= 0:
        return 0
    row, place = divmod(level - 1, VOWELS)
    rows_below = ROW_POINTS * VOWELS * row * (row + 1) // 2
    return rows_below + (place + 1) * ROW_POINTS * (row + 1)


def name_of(level: int) -> str | None:
    """단계의 이름 한 글자. 0단계는 이름이 없다"""
    if level <= 0:
        return None
    return chr(FIRST_SYLLABLE + (level - 1) * FINALS)


def label_of(level: int) -> str:
    """화면에 적는 말. 홑낫표로 감싼다 — 「개」처럼 혼자 두면 뜻이 생기는 글자가 있어서 (D-100)"""
    name = name_of(level)
    return "아직 레벨이 없어요" if name is None else f"「{name}」 단계"


def next_score(level: int) -> int | None:
    """다음 단계까지 필요한 점수. 끝까지 올라갔으면 None"""
    return None if level >= MAX_LEVEL else score_for(level + 1)


def standing(sentence_count: int, received_up_count: int) -> dict:
    """화면이 쓰는 한 묶음 (점수·단계·이름·다음 단계)"""
    points = score(sentence_count, received_up_count)
    level = level_of(points)
    return {
        "score": points,
        "level": level,
        "level_name": name_of(level),
        "level_label": label_of(level),
        "next_score": next_score(level),
    }
