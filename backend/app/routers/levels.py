"""레벨 화면 (D-100)

로그인하지 않아도 볼 수 있음 — 단계마다 몇 명인지는 누구에게나 같은 숫자
"""

from fastapi import APIRouter

from app.deps import DbSession
from app.schemas.level import LevelDistributionOut
from app.services import standings as standing_service

router = APIRouter(prefix="/api/levels", tags=["levels"])


@router.get("/distribution")
def get_distribution(db: DbSession) -> LevelDistributionOut:
    """단계별 작가 수 (한 명이라도 있는 단계만)"""
    return standing_service.distribution(db)
