"""스토리 추천 (docs 07 추천, F-13)

1인 1회 · 같은 버튼을 다시 누르면 취소 · 자기 스토리에는 추천 불가 (D-54)
"""

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.errors import api_error
from app.models import Story, StoryRecommendation, User
from app.schemas.story import StoryOut
from app.services.stories import find_visible_story, get_story


def add_recommendation(db: Session, user: User, story_id: int) -> StoryOut:
    """추천 누르기. 이미 추천했으면 그대로 둠"""
    story = _recommendable(db, user, story_id)

    # 거의 동시에 두 번 눌려도 중복으로 터지지 않게 DB가 한 번에 처리 (이미 있으면 그대로)
    db.execute(
        insert(StoryRecommendation)
        .values(user_id=user.id, story_id=story.id)
        .on_conflict_do_nothing(
            index_elements=[StoryRecommendation.user_id, StoryRecommendation.story_id]
        )
    )
    db.commit()
    return get_story(db, story_id, user_id=user.id)


def remove_recommendation(db: Session, user: User, story_id: int) -> StoryOut:
    """내 추천 취소 (안 눌렀어도 그냥 성공)"""
    _recommendable(db, user, story_id)

    found = db.get(StoryRecommendation, {"user_id": user.id, "story_id": story_id})
    if found is not None:
        db.delete(found)
        db.commit()
    return get_story(db, story_id, user_id=user.id)


def _recommendable(db: Session, user: User, story_id: int) -> Story:
    """추천할 수 있는 스토리인지 확인 (없음·숨김 404 / 자기 스토리 403 / 첫 문장 접힘 409)"""
    story, root_status = find_visible_story(db, story_id)
    if story.creator_id == user.id:
        raise api_error(403, "SELF_RECOMMEND", "자기 스토리에는 추천할 수 없어요")
    if root_status != "active":
        # 첫 문장이 신고로 접힌 스토리는 내용이 가려진 셈 → 반응도 받지 않음 (D-82와 같은 이유)
        raise api_error(409, "RECOMMEND_NOT_ALLOWED", "지금은 추천할 수 없는 스토리예요")
    return story
