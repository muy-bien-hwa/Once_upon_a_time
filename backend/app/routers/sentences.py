"""문장 API 주소 (docs 07 #6~#8)"""

from fastapi import APIRouter

from app.deps import CurrentAuthor, CurrentUser, DbSession, OptionalUser
from app.schemas.report import ReportCreate, ReportOut
from app.schemas.sentence import (
    PathOut,
    SentenceCreate,
    SentenceListOut,
    SentenceOut,
    SentenceSort,
    VoteCreate,
)
from app.services import reports as report_service
from app.services import sentences as sentence_service
from app.services import votes as vote_service

router = APIRouter(prefix="/api/sentences", tags=["sentences"])


@router.get("/{sentence_id}/path")
def get_path(sentence_id: int, db: DbSession) -> PathOut:
    """첫 문장부터 이 문장까지 (#6) — 공유 주소 /s/{id} 화면이 씀"""
    return sentence_service.get_path(db, sentence_id)


@router.get("/{sentence_id}/children")
def list_children(
    sentence_id: int, db: DbSession, user: OptionalUser, sort: SentenceSort = "score"
) -> SentenceListOut:
    """이어진 문장들 (#7). 로그인했으면 내가 누른 표도 함께"""
    items = sentence_service.list_children(db, sentence_id, sort, user_id=user.id if user else None)
    return SentenceListOut(items=items)


@router.post("/{sentence_id}/children", status_code=201)
def add_child(
    sentence_id: int, data: SentenceCreate, db: DbSession, user: CurrentAuthor
) -> SentenceOut:
    """이어 쓰기 (#8)"""
    return sentence_service.add_child(db, user, sentence_id, data.content)


@router.delete("/{sentence_id}")
def delete_sentence(sentence_id: int, db: DbSession, user: CurrentUser) -> dict[str, str]:
    """내 문장 지우기 (F-09) — "removed"(사라짐) 또는 "deleted"(자리만 남음)를 알려 줌"""
    return {"status": sentence_service.delete_sentence(db, user, sentence_id)}


@router.put("/{sentence_id}/vote")
def set_vote(sentence_id: int, data: VoteCreate, db: DbSession, user: CurrentUser) -> SentenceOut:
    """추천·비추천 누르기 (F-07)"""
    return vote_service.set_vote(db, user, sentence_id, data.value)


@router.delete("/{sentence_id}/vote")
def clear_vote(sentence_id: int, db: DbSession, user: CurrentUser) -> SentenceOut:
    """내 표 취소 (F-07)"""
    return vote_service.clear_vote(db, user, sentence_id)


@router.post("/{sentence_id}/reports", status_code=201)
def report_sentence(
    sentence_id: int, data: ReportCreate, db: DbSession, user: CurrentUser
) -> ReportOut:
    """문장 신고 (#31, F-10). 신고 수는 아무에게도 보여주지 않음 (D-93)"""
    report_service.report_sentence(db, user, sentence_id, data)
    return ReportOut()
