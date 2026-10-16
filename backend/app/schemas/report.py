"""신고 API가 주고받는 데이터 모양 (docs 07 신고, F-10·D-93)"""

from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

# 사유는 7종 중 하나만 고름 (화면 토글과 같은 순서)
# 모델의 REASONS와 같아야 함 (test_report_api에서 확인)
ReportReason = Literal["abuse", "sexual", "violence", "spam", "privacy", "plagiarism", "other"]

# 설명은 500자 이내 / "기타"를 고르면 반드시 적어야 함 (서비스에서 확인)
ReportDetail = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class ReportCreate(BaseModel):
    reason: ReportReason
    detail: ReportDetail = ""


class ReportOut(BaseModel):
    """신고 수는 아무에게도 보여주지 않음 → 접수됐다는 사실만 알려 줌 (D-93)"""

    reported: bool = True
