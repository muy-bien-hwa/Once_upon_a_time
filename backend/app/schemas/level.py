"""레벨 화면이 보내는 데이터 모양 (D-100)"""

from pydantic import BaseModel


class LevelCountOut(BaseModel):
    level: int
    # 그 단계의 이름 한 글자 (「가」~「히」)
    name: str
    count: int


class LevelDistributionOut(BaseModel):
    # 한 명이라도 있는 단계만, 낮은 단계부터
    items: list[LevelCountOut]
    # 레벨이 있는(1단계 이상) 작가 수
    total_writers: int
