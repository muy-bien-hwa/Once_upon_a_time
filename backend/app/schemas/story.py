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
    # 스토리를 시작한 작가 = 첫 문장을 쓴 사람 (읽기 화면 정보 칸)
    creator_nickname: str
    recommend_count: int
    # 내가 이 스토리를 추천했는지 (로그인 안 했으면 항상 false, F-13)
    my_recommendation: bool
    # 참여한 작가 수: 이 스토리에 문장을 한 번이라도 쓴 고유 유저 (D-24·D-38)
    author_count: int
    max_depth: int
    # 커뮤니티 탭에 적는 글 개수 (F-17)
    post_count: int
    created_at: datetime


class StoryListOut(BaseModel):
    items: list[StoryOut]
    page: int
    size: int
    total: int


class StoryCreateOut(BaseModel):
    story: StoryOut
    sentence: SentenceOut


class StoryAuthor(BaseModel):
    """스토리 작가 목록의 한 줄 (D-91)"""

    user_id: int
    nickname: str
    sentence_count: int
    # 창시자 = 금색 만년필, 관리자 = 은색 만년필 (화면 표시)
    is_creator: bool
    is_manager: bool


class StoryAuthorsOut(BaseModel):
    items: list[StoryAuthor]
    # 내가 관리자를 임명·해임할 수 있는지 (스토리를 시작한 작가만)
    can_appoint: bool
    # 내가 글을 고정할 수 있는지 (창시자 + 관리자)
    can_pin: bool
