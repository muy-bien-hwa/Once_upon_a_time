"""마이페이지·작가 화면이 주고받는 데이터 모양 (docs 07 #34~#37, D-95)"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# 내 문장·작가의 문장 목록 정렬: 최신순(기본) / 추천순
ProfileSort = Literal["latest", "votes"]

# 내 문장 거르개: 전체(기본) / 보임 / 삭제함 / 신고 처리됨
ProfileFilter = Literal["all", "active", "deleted", "folded"]


class MeSummaryOut(BaseModel):
    """마이페이지 맨 위 칸 (나만 봄)"""

    joined_at: datetime
    # 아래 숫자 셋은 모두 "목록에 보이는 문장"과 같은 범위 → 숫자와 목록이 어긋나지 않음
    sentence_count: int
    story_count: int
    received_up_count: int
    # 그중 지금 그대로 보이는 문장 (지우거나 접힌 것을 뺀 수)
    live_sentence_count: int


class AuthorOut(BaseModel):
    """작가 화면 맨 위 칸 (누구나 봄) — 보이는 문장만 센다"""

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
