"""유저 찾기·만들기 (3단계 F-06)"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

GOOGLE = "google"


def get_or_create_google_user(db: Session, google_user_id: str) -> User:
    """구글 계정으로 처음 온 사람이면 유저를 만듦 (닉네임은 아직 비어 있음, D-48)

    google_user_id = 구글이 주는 사람 고유 번호(sub). 이메일이 바뀌어도 그대로라 이걸 기준으로 함
    """
    user = db.scalar(
        select(User).where(User.provider == GOOGLE, User.provider_user_id == google_user_id)
    )
    if user is None:
        user = User(provider=GOOGLE, provider_user_id=google_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
