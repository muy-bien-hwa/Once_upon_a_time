"""추천 정렬 점수 (docs 04-ranking-score, D-37)

문장 목록과 포럼 Hot 정렬이 같은 공식을 씀 (설정값만 다름)

score = V(투표점수) + N(새 문장 가산점) + J(흔들기)
"""

import hashlib
import math


def rank_score(
    *,
    up: int,
    down: int,
    age_hours: float,
    user_id: int | None,
    item_id: int,
    kst_date: str,
    b: float,
    h: float,
    j0: float,
) -> float:
    v = up - down
    # 표가 늘수록 효과가 둔해짐: +9 → 1, +99 → 2, -9 → -1
    vote_score = math.copysign(math.log10(1 + abs(v)), v)
    # 막 쓴 문장은 b점에서 시작해 h시간마다 절반으로 줄어듦
    new_bonus = b * 0.5 ** (age_hours / h)
    # 같은 사람·같은 날이면 항상 같은 값(-1~+1) → 순서가 새로고침마다 바뀌지 않음
    seed = f"{kst_date}:{user_id or 0}:{item_id}".encode()
    r = int(hashlib.sha256(seed).hexdigest()[:8], 16) / 0xFFFFFFFF * 2 - 1
    return vote_score + new_bonus + j0 * r
