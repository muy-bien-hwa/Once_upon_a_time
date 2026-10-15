"""포럼 API가 주고받는 데이터 모양 (docs 07 포럼, D-42·D-91)"""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

# 글 제목 100자 · 본문 5,000자 (D-51) / 제목은 줄바꿈 금지
PostTitle = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[^\r\n]*$"),
]
PostBody = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
# 댓글 1,000자 (D-51)
CommentBody = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]

# 목록 정렬: new = 최신순(기본) / hot = 점수순 (D-42·D-91)
PostSort = Literal["new", "hot"]


class PostCreate(BaseModel):
    title: PostTitle
    body: PostBody
    # 문장 1개 인용 (D-42). 읽기 화면에서 넘어오면 채워져 있음
    quoted_sentence_id: int | None = None


class QuotedSentence(BaseModel):
    """글에 끌어온 문장 (누르면 그 문장으로 이동)"""

    id: int
    content: str


class PostSummary(BaseModel):
    """목록에 보이는 글 (본문은 빼고 보냄 → 목록이 가벼움)"""

    id: int
    story_id: int
    title: str
    author_nickname: str
    created_at: datetime
    up_count: int
    down_count: int
    # 내가 누른 표: 1·-1·null (로그인 안 했으면 항상 null)
    my_vote: int | None
    comment_count: int
    # 1·2 = 고정 자리 / null = 보통 글 (스토리당 2개까지, D-91)
    pin_slot: int | None
    quoted_sentence: QuotedSentence | None


class PostOut(PostSummary):
    """글 하나 화면"""

    body: str


class PostListOut(BaseModel):
    items: list[PostSummary]
    page: int
    size: int
    total: int


class CommentCreate(BaseModel):
    body: CommentBody
    # 답글이면 그 댓글 번호 (답글에 다는 답글도 받음 → 서버가 윗 댓글로 올려 붙임, D-91)
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    post_id: int
    # 답글이 매달린 윗 댓글 (null이면 맨 위 댓글)
    parent_id: int | None
    # 신고로 접히면 내용·작성자를 비움 (D-69와 같은 방식)
    body: str | None
    author_nickname: str | None
    status: Literal["active", "folded"]
    # 누구에게 한 말인지 (@닉네임) — 지금 닉네임으로 보냄 (D-91)
    reply_to_nickname: str | None
    created_at: datetime


class CommentListOut(BaseModel):
    items: list[CommentOut]


class VoteCreate(BaseModel):
    # 1 = 추천, -1 = 비추천
    value: Literal[1, -1]
