"""문장 API 주소 (docs 07 #6~#8)"""

from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas.sentence import PathOut, SentenceCreate, SentenceListOut, SentenceOut, SentenceSort
from app.services import sentences as sentence_service

router = APIRouter(prefix="/api/sentences", tags=["sentences"])


@router.get("/{sentence_id}/path")
def get_path(sentence_id: int, db: DbSession) -> PathOut:
    """첫 문장부터 이 문장까지 (#6) — 공유 주소 /s/{id} 화면이 씀"""
    return sentence_service.get_path(db, sentence_id)


@router.get("/{sentence_id}/children")
def list_children(sentence_id: int, db: DbSession, sort: SentenceSort = "score") -> SentenceListOut:
    """이어진 문장들 (#7)"""
    items = sentence_service.list_children(db, sentence_id, sort, user_id=None)
    return SentenceListOut(items=items)


@router.post("/{sentence_id}/children", status_code=201)
def add_child(
    sentence_id: int, data: SentenceCreate, db: DbSession, user: CurrentUser
) -> SentenceOut:
    """이어 쓰기 (#8)"""
    return sentence_service.add_child(db, user, sentence_id, data.content)
