"""작가 화면 (docs 07 #36·#37, D-95)

로그인하지 않아도 볼 수 있음 — 닉네임·문장은 이미 화면에 공개된 것들
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app.deps import DbSession
from app.schemas.profile import AuthorOut, ProfileSentenceListOut, ProfileSort
from app.services import profiles as profile_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/{nickname}")
def get_author(nickname: str, db: DbSession) -> AuthorOut:
    """작가 한 명 (#36). 없는 닉네임도 탈퇴한 사람도 똑같이 404"""
    return profile_service.author(db, nickname)


@router.get("/{nickname}/sentences")
def author_sentences(
    nickname: str,
    db: DbSession,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=50)] = 20,
    sort: ProfileSort = "latest",
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> ProfileSentenceListOut:
    """그 작가가 쓴 문장 (#37). 지운 문장·접힌 문장은 나오지 않음"""
    return profile_service.author_sentences(db, nickname, page, size, sort, q)
