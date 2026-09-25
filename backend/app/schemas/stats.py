"""기록·Hot API가 보내는 데이터 모양 (docs 07 #9~#11)"""

from typing import Literal

from pydantic import BaseModel

from app.schemas.sentence import SentenceOut, StoryRef
from app.schemas.story import StoryOut

# 일간(오늘 0시부터) · 주간(7일) · 월간(30일), 한국 시간 기준
HotPeriod = Literal["day", "week", "month"]


class RecordOut(BaseModel):
    # 참여 작가가 가장 많은 스토리 (기네스 기록과 비교해서 보여줌) / 스토리가 없으면 null
    most_authors_story: StoryOut | None


class HotStory(BaseModel):
    story: StoryOut
    # 그 기간에 받은 추천 수
    recommend_count: int


class HotStories(BaseModel):
    day: list[HotStory]
    week: list[HotStory]
    month: list[HotStory]


class HotSentence(BaseModel):
    sentence: SentenceOut
    # 어느 스토리에서 뻗어 나온 문장인지
    story: StoryRef
    # 그 기간에 받은 추천 − 비추천
    vote_count: int


class HotSentences(BaseModel):
    day: list[HotSentence]
    week: list[HotSentence]
    month: list[HotSentence]
