"""하루 제한 (F-08, D-49·D-90)

- 같은 스토리에 하루 10문장 · 새 스토리는 하루 5개
- 하루 기준은 한국 시간 0시 (Hot의 일간 집계와 같은 기준)
- 개수를 따로 저장하지 않고 그때그때 셈 (D-44) / 지운 문장도 셈 (D-90)
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models import ForumComment, ForumPost, Sentence, Story, User
from app.timeutil import kst_today_start

STORIES_PER_DAY = 5
SENTENCES_PER_STORY_PER_DAY = 10
POSTS_PER_DAY = 10
COMMENTS_PER_DAY = 50


def _lock_user(db: Session, user: User) -> None:
    """같은 사람이 거의 동시에 두 번 보내도 한 줄로 세워서 처리 (제한을 정확히 세려고)

    이 요청이 끝날 때까지 그 사람의 users 줄을 잡아 둠 → 둘 다 "아직 4개"로 보고 통과하는 일이 없음
    """
    db.execute(select(User.id).where(User.id == user.id).with_for_update())


def check_new_story(db: Session, user: User) -> None:
    """오늘 연 스토리가 5개가 되면 더 못 열게 막음"""
    _lock_user(db, user)
    opened = db.scalar(
        select(func.count())
        .select_from(Story)
        .where(Story.creator_id == user.id, Story.created_at >= kst_today_start())
    )
    if opened >= STORIES_PER_DAY:
        raise api_error(
            429,
            "DAILY_STORY_LIMIT",
            f"새 스토리는 하루 {STORIES_PER_DAY}개까지 열 수 있어요. 내일 다시 열어 주세요",
        )


def check_new_sentence(db: Session, user: User, story_id: int) -> None:
    """오늘 이 스토리에 쓴 문장이 10개가 되면 더 못 쓰게 막음 (지운 문장도 셈)"""
    _lock_user(db, user)
    written = db.scalar(
        select(func.count())
        .select_from(Sentence)
        .where(
            Sentence.story_id == story_id,
            Sentence.author_id == user.id,
            Sentence.created_at >= kst_today_start(),
        )
    )
    if written >= SENTENCES_PER_STORY_PER_DAY:
        raise api_error(
            429,
            "DAILY_SENTENCE_LIMIT",
            f"한 스토리에는 하루 {SENTENCES_PER_STORY_PER_DAY}문장까지 쓸 수 있어요. "
            "다른 스토리에 이어 쓰거나 내일 다시 와 주세요",
        )


def check_new_post(db: Session, user: User) -> None:
    """오늘 쓴 포럼 글이 10개가 되면 더 못 쓰게 막음 (D-91)"""
    _lock_user(db, user)
    written = db.scalar(
        select(func.count())
        .select_from(ForumPost)
        .where(ForumPost.author_id == user.id, ForumPost.created_at >= kst_today_start())
    )
    if written >= POSTS_PER_DAY:
        raise api_error(
            429,
            "DAILY_POST_LIMIT",
            f"커뮤니티 글은 하루 {POSTS_PER_DAY}개까지 쓸 수 있어요. 내일 다시 써 주세요",
        )


def check_new_comment(db: Session, user: User) -> None:
    """오늘 쓴 댓글이 50개가 되면 더 못 쓰게 막음 (D-91)"""
    _lock_user(db, user)
    written = db.scalar(
        select(func.count())
        .select_from(ForumComment)
        .where(ForumComment.author_id == user.id, ForumComment.created_at >= kst_today_start())
    )
    if written >= COMMENTS_PER_DAY:
        raise api_error(
            429,
            "DAILY_COMMENT_LIMIT",
            f"댓글은 하루 {COMMENTS_PER_DAY}개까지 쓸 수 있어요. 내일 다시 써 주세요",
        )
