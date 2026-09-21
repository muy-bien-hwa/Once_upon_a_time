"""스토리 API가 주고받는 데이터 모양 (docs 07)"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.schemas.sentence import SentenceOut, SentenceText

# 스토리 제목: 앞뒤 공백을 지운 뒤 1~50자, 줄바꿈 금지
StoryTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50, pattern=r"^[^\r\n]*$"),
]

StorySort = Literal["latest", "oldest", "recommended", "deepest", "shallowest"]


class StoryCreate(BaseModel):
    title: StoryTitle
    content: SentenceText


class StoryOut(BaseModel):
    id: int
    title: str
    # 첫 문장 id → 목록에서 스토리를 누르면 /s/{first_sentence_id}로 이동 (D-65)
    first_sentence_id: int
    # 첫 문장 내용 (목록 카드 미리보기) / 신고로 접히면 null (D-69)
    first_sentence: str | None
    # folded면 카드에 "신고 처리된 문장입니다."만 표시 (D-69)
    first_sentence_status: Literal["active", "folded"]
    recommend_count: int
    # 참여한 작가 수: 이 스토리에 문장을 한 번이라도 쓴 고유 유저 (D-24·D-38)
    author_count: int
    max_depth: int
    created_at: datetime


class StoryListOut(BaseModel):
    items: list[StoryOut]
    page: int
    size: int
    total: int


class StoryCreateOut(BaseModel):
    story: StoryOut
    sentence: SentenceOut
