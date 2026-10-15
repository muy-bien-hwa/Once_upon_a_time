"""스토리 작가 목록과 스토리 관리자 (D-91)

- 관리자를 임명·해임할 수 있는 사람: 그 스토리를 시작한 작가 한 명뿐
- 관리자가 할 수 있는 일: 커뮤니티 글 고정·해제 (남의 글을 지우지는 못함)
- 임명 대상: 그 스토리에 문장을 한 번이라도 쓴 작가
"""

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models import Sentence, Story, StoryManager, User
from app.schemas.story import StoryAuthor, StoryAuthorsOut
from app.services.stories import find_visible_story


def list_authors(db: Session, story_id: int, user_id: int | None = None) -> StoryAuthorsOut:
    """그 스토리에 문장을 쓴 작가들 (많이 쓴 순) + 내가 할 수 있는 일"""
    story, _ = find_visible_story(db, story_id)
    manager_ids = _manager_ids(db, story_id)

    rows = db.execute(
        select(User.id, User.nickname, func.count(Sentence.id))
        .join(Sentence, Sentence.author_id == User.id)
        .where(Sentence.story_id == story_id, Sentence.status != "removed")
        .group_by(User.id, User.nickname)
        .order_by(func.count(Sentence.id).desc(), User.id)
    ).all()

    items = [
        StoryAuthor(
            user_id=author_id,
            nickname=nickname,
            sentence_count=count,
            is_creator=author_id == story.creator_id,
            is_manager=author_id in manager_ids,
        )
        for author_id, nickname, count in rows
    ]
    return StoryAuthorsOut(
        items=items,
        can_appoint=user_id is not None and user_id == story.creator_id,
        can_pin=_can_pin(story, manager_ids, user_id),
    )


def appoint(db: Session, user: User, story_id: int, target_id: int) -> StoryAuthorsOut:
    """관리자로 임명 (스토리를 시작한 작가만)"""
    story = _only_creator(db, user, story_id)
    _must_be_author(db, story.id, target_id)
    if target_id == story.creator_id:
        raise api_error(409, "ALREADY_CREATOR", "스토리를 시작한 작가는 이미 권한이 있어요")

    db.execute(
        insert(StoryManager)
        .values(story_id=story.id, user_id=target_id)
        .on_conflict_do_nothing(index_elements=[StoryManager.story_id, StoryManager.user_id])
    )
    db.commit()
    return list_authors(db, story_id, user_id=user.id)


def dismiss(db: Session, user: User, story_id: int, target_id: int) -> StoryAuthorsOut:
    """관리자 권한 거두기 (안 가진 사람이어도 그냥 성공)"""
    story = _only_creator(db, user, story_id)

    found = db.get(StoryManager, {"story_id": story.id, "user_id": target_id})
    if found is not None:
        db.delete(found)
        db.commit()
    return list_authors(db, story_id, user_id=user.id)


def can_pin(db: Session, story_id: int, user_id: int | None) -> bool:
    """글을 고정할 수 있는 사람인지 (창시자 + 관리자)"""
    story = db.get(Story, story_id)
    if story is None:
        return False
    return _can_pin(story, _manager_ids(db, story_id), user_id)


def require_pin_permission(db: Session, story_id: int, user_id: int) -> None:
    if not can_pin(db, story_id, user_id):
        raise api_error(
            403, "PIN_NOT_ALLOWED", "스토리를 시작한 작가와 관리자만 글을 고정할 수 있어요"
        )


def _can_pin(story: Story, manager_ids: set[int], user_id: int | None) -> bool:
    return user_id is not None and (user_id == story.creator_id or user_id in manager_ids)


def _manager_ids(db: Session, story_id: int) -> set[int]:
    return set(
        db.scalars(select(StoryManager.user_id).where(StoryManager.story_id == story_id)).all()
    )


def _only_creator(db: Session, user: User, story_id: int) -> Story:
    story, _ = find_visible_story(db, story_id)
    if story.creator_id != user.id:
        raise api_error(
            403, "NOT_STORY_CREATOR", "스토리를 시작한 작가만 권한을 주고 거둘 수 있어요"
        )
    return story


def _must_be_author(db: Session, story_id: int, target_id: int) -> None:
    written = db.scalar(
        select(Sentence.id)
        .where(
            Sentence.story_id == story_id,
            Sentence.author_id == target_id,
            Sentence.status != "removed",
        )
        .limit(1)
    )
    if written is None:
        raise api_error(
            404, "NOT_STORY_AUTHOR", "이 스토리에 문장을 쓴 작가만 관리자로 정할 수 있어요"
        )
