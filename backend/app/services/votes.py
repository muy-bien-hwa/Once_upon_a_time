"""문장 투표 (docs 07 투표, F-07)

1인 1표 · 같은 버튼을 다시 누르면 취소 · 추천↔비추천은 바로 바뀜 (D-52·D-82)
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models import Sentence, SentenceVote, User
from app.schemas.sentence import SentenceOut
from app.services.sentences import get_sentence


def set_vote(db: Session, user: User, sentence_id: int, value: int) -> SentenceOut:
    """추천(1)·비추천(-1) 누르기. 이미 같은 표가 있으면 그대로 둠"""
    sentence = _votable(db, user, sentence_id)

    vote = db.get(SentenceVote, {"user_id": user.id, "sentence_id": sentence.id})
    if vote is None:
        db.add(SentenceVote(user_id=user.id, sentence_id=sentence.id, value=value))
    else:
        vote.value = value
    db.commit()
    return get_sentence(db, sentence_id, user_id=user.id)


def clear_vote(db: Session, user: User, sentence_id: int) -> SentenceOut:
    """내 표 취소 (안 눌렀어도 그냥 성공)"""
    _votable(db, user, sentence_id)

    vote = db.get(SentenceVote, {"user_id": user.id, "sentence_id": sentence_id})
    if vote is not None:
        db.delete(vote)
        db.commit()
    return get_sentence(db, sentence_id, user_id=user.id)


def _votable(db: Session, user: User, sentence_id: int) -> Sentence:
    """투표할 수 있는 문장인지 확인 (없음·숨김 404 / 접힘·삭제 409 / 자기 문장 403)"""
    sentence = db.scalar(select(Sentence).where(Sentence.id == sentence_id))
    if sentence is None or sentence.status == "removed":
        raise api_error(404, "SENTENCE_NOT_FOUND", "없거나 사라진 문장이에요")
    if sentence.status != "active":
        # 내용이 가려진 문장에는 투표할 수 없음 (D-82)
        raise api_error(409, "VOTE_NOT_ALLOWED", "지금은 투표할 수 없는 문장이에요")
    if sentence.author_id == user.id:
        raise api_error(403, "SELF_VOTE", "자기 문장에는 투표할 수 없어요")
    return sentence
