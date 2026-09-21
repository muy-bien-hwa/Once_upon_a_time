"""문장 API가 주고받는 데이터 모양 (docs 07)"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

# 문장 본문: 앞뒤 공백을 지운 뒤 1~100자, 줄바꿈 금지 (D-61)
SentenceText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[^\r\n]*$"),
]

# 문장 목록 정렬: score = 투표 + 최신성(기본) / votes = 추천순 / latest = 날짜순 (D-60)
SentenceSort = Literal["score", "votes", "latest"]


class SentenceCreate(BaseModel):
    content: SentenceText


class SentenceOut(BaseModel):
    id: int
    story_id: int
    parent_id: int | None
    depth: int
    # 삭제된 문장·신고로 접힌 문장은 본문·작성자를 비움 (D-63·D-69)
    content: str | None
    status: Literal["active", "folded", "deleted"]
    author_nickname: str | None
    created_at: datetime
    up_count: int
    down_count: int
    # 이어진 문장 수 → 화면 오른쪽 회색 박스 개수 (D-59)
    child_count: int


class SentenceListOut(BaseModel):
    items: list[SentenceOut]


class StoryRef(BaseModel):
    id: int
    title: str


class PathOut(BaseModel):
    """첫 문장부터 현재 문장까지 (공유 주소 /s/{id}가 쓰는 데이터)"""

    story: StoryRef
    items: list[SentenceOut]
