"""마이페이지·작가 화면이 주고받는 데이터 모양 (docs 07 #34~#37, D-95)"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# 내 문장·작가의 문장 목록 정렬: 최신순(기본) / 추천순
ProfileSort = Literal["latest", "votes"]

# 내 문장 거르개: 전체(기본) / 보임 / 삭제함 / 신고 처리됨
ProfileFilter = Literal["all", "active", "deleted", "folded"]


class LevelOut(BaseModel):
    """레벨 칸 — levels.standing()이 주는 그대로 (D-100)

    점수는 내 화면이든 작가 화면이든 "내 문장" 범위(지운 것·접힌 것까지)로 셈
    → 문장을 지워도 레벨이 내려가지 않고, 남이 보는 레벨도 내가 보는 것과 같다
    """

    score: int
    level: int
    # 아직 한 문장도 없으면 0단계 → 이름이 없음
    level_name: str | None
    level_label: str
    # 지금 단계가 시작된 점수 (진행 막대를 이 단계 안에서 그리라고)
    level_score: int
    # 다음 단계가 되는 점수. 끝까지 올라갔으면 null
    next_score: int | None


class MeSummaryOut(LevelOut):
    """마이페이지 맨 위 칸 (나만 봄)"""

    joined_at: datetime
    # 아래 숫자 셋은 모두 "목록에 보이는 문장"과 같은 범위 → 숫자와 목록이 어긋나지 않음
    sentence_count: int
    story_count: int
    received_up_count: int
    # 그중 지금 그대로 보이는 문장 (지우거나 접힌 것을 뺀 수)
    live_sentence_count: int


class AuthorOut(LevelOut):
    """작가 화면 맨 위 칸 (누구나 봄) — 숫자는 보이는 문장만 세고, 레벨만 예외 (LevelOut 설명 참고)"""

    nickname: str
    # 날짜까지는 공개하지 않기로 함 (D-95) → "2026-05"
    joined_month: str
    sentence_count: int
    story_count: int
    received_up_count: int


class ProfileSentenceOut(BaseModel):
    id: int
    # 지운 문장·접힌 문장은 본문을 보내지 않음 (내 화면에서도, 약관 26조)
    content: str | None
    status: Literal["active", "folded", "deleted"]
    story_id: int
    story_title: str
    created_at: datetime
    up_count: int


class ProfileCounts(BaseModel):
    """거르개 버튼에 적는 수 — 검색 중이면 그 검색 안에서의 수"""

    all: int
    active: int
    deleted: int
    folded: int


class ProfileSentenceListOut(BaseModel):
    items: list[ProfileSentenceOut]
    page: int
    size: int
    # 지금 고른 거르개(와 검색)에 해당하는 문장 수
    total: int
    # 내 화면에서만 채움 (작가 화면은 보이는 문장뿐이라 거를 것이 없음)
    counts: ProfileCounts | None = None


# 점수가 생긴 일 한 가지: 문장을 쓴 일 / 추천을 받은 일
ScoreEventKind = Literal["sentence", "up"]


class ScoreEventOut(BaseModel):
    """점수가 어디서 왔는지 한 줄 (D-100)"""

    kind: ScoreEventKind
    # 문장 하나 10점 · 추천 하나 1점 (levels.py의 숫자를 그대로 씀)
    points: int
    # 문장을 쓴 시각 / 추천을 받은 시각
    at: datetime
    story_id: int
    story_title: str
    sentence_id: int
    # 지운 문장·접힌 문장은 본문을 보내지 않음 (내 화면에서도, 약관 26조)
    sentence_content: str | None


class ScoreHistoryOut(BaseModel):
    items: list[ScoreEventOut]
    page: int
    size: int
    # 점수가 생긴 일의 전체 수 (= 문장 수 + 받은 추천 수)
    total: int
