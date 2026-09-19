# 모든 모델을 여기서 불러와야 Alembic이 테이블을 빠짐없이 인식함
from app.models.base import Base
from app.models.forum import ForumComment, ForumPost, ForumPostVote
from app.models.report import Report
from app.models.sentence import Sentence, SentenceVote
from app.models.story import Story, StoryRecommendation
from app.models.user import User

__all__ = [
    "Base",
    "ForumComment",
    "ForumPost",
    "ForumPostVote",
    "Report",
    "Sentence",
    "SentenceVote",
    "Story",
    "StoryRecommendation",
    "User",
]
