"""스토리 조회·생성 (docs 07 #1~#3)

스토리 = 제목 + 첫 문장 1개 (D-65). 첫 문장은 스토리를 만들 때 함께 저장
"""

from sqlalchemy import Row, and_, func, select
from sqlalchemy.orm import Session, aliased

from app.errors import api_error
from app.models import Sentence, Story, StoryRecommendation, User
from app.schemas.story import StoryCreate, StoryCreateOut, StoryListOut, StoryOut, StorySort
from app.services.sentences import get_sentence

# 스토리의 첫 문장 (스토리당 1개, D-65) → 스토리와 1:1로 붙여서 조회
_root = aliased(Sentence)
_root_join = (_root, and_(_root.story_id == Story.id, _root.parent_id.is_(None)))
# 보이는 스토리 = 첫 문장이 숨김(removed) 상태가 아님 (docs 05 "스토리 숨김")
_visible = _root.status != "removed"

# 스토리마다 붙이는 값 (저장하지 않고 조회할 때 계산)
_recommend_count = (
    select(func.count()).where(StoryRecommendation.story_id == Story.id).scalar_subquery()
)
# 참여한 작가 수: 문장을 한 번이라도 쓴 고유 유저, 지운 문장 포함 (D-24·D-38)
_author_count = (
    select(func.count(func.distinct(Sentence.author_id)))
    .where(Sentence.story_id == Story.id)
    .scalar_subquery()
)
_max_depth = (
    select(func.coalesce(func.max(Sentence.depth), 0))
    .where(Sentence.story_id == Story.id, Sentence.status != "removed")
    .scalar_subquery()
)

# 정렬 (D-58): 같으면 최신순
_SORTS = {
    "latest": (Story.created_at.desc(), Story.id.desc()),
    "oldest": (Story.created_at.asc(), Story.id.asc()),
    "recommended": (_recommend_count.desc(), Story.created_at.desc(), Story.id.desc()),
    "deepest": (_max_depth.desc(), Story.created_at.desc(), Story.id.desc()),
    "shallowest": (_max_depth.asc(), Story.created_at.desc(), Story.id.desc()),
}


def list_stories(db: Session, sort: StorySort, page: int, size: int) -> StoryListOut:
    total = db.scalar(select(func.count()).select_from(Story).join(*_root_join).where(_visible))
    rows = db.execute(
        _select_stories().order_by(*_SORTS[sort]).offset((page - 1) * size).limit(size)
    )
    return StoryListOut(items=[_to_out(row) for row in rows], page=page, size=size, total=total)


def get_story(db: Session, story_id: int) -> StoryOut:
    """스토리 1개. 없거나 숨겨진 스토리면 404"""
    row = db.execute(_select_stories().where(Story.id == story_id)).first()
    if row is None:
        raise api_error(404, "STORY_NOT_FOUND", "없는 스토리예요")
    return _to_out(row)


def create_story(db: Session, user: User, data: StoryCreate) -> StoryCreateOut:
    """스토리와 첫 문장을 한 번에 저장 (둘 다 저장되거나 둘 다 취소)"""
    story = Story(title=data.title, creator_id=user.id)
    db.add(story)
    db.flush()
    first = Sentence(story_id=story.id, author_id=user.id, content=data.content, depth=0)
    db.add(first)
    db.commit()
    return StoryCreateOut(story=get_story(db, story.id), sentence=get_sentence(db, first.id))


def _select_stories():
    return (
        select(
            Story,
            _root.id,
            _root.content,
            _root.status,
            _recommend_count,
            _author_count,
            _max_depth,
        )
        .join(*_root_join)
        .where(_visible)
    )


def _to_out(row: Row) -> StoryOut:
    story, root_id, root_content, root_status, recommend_count, author_count, max_depth = row
    return StoryOut(
        id=story.id,
        title=story.title,
        first_sentence_id=root_id,
        # 신고로 접힌 첫 문장은 내용을 보내지 않음 (D-69)
        first_sentence=root_content if root_status == "active" else None,
        first_sentence_status=root_status,
        recommend_count=recommend_count,
        author_count=author_count,
        max_depth=max_depth,
        created_at=story.created_at,
    )
