"""한국 시간(KST) 계산은 모두 여기서 (docs 05 "시간")"""

from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def kst_now() -> datetime:
    return datetime.now(KST)


def kst_today_start() -> datetime:
    """오늘 한국 시간 0시 → 하루 제한(D-41)의 기준"""
    return kst_now().replace(hour=0, minute=0, second=0, microsecond=0)
