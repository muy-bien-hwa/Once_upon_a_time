"""유저 찾기·만들기·탈퇴 (3단계 F-06, 6-4 탈퇴 추가)"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

GOOGLE = "google"

# 탈퇴한 사람이 쓴 문장·글에 대신 보여 줄 이름
WITHDRAWN = "탈퇴한 작가"


def name_of(nickname: str | None) -> str:
    """화면에 보일 작가 이름 — 닉네임이 비어 있으면 탈퇴한 사람

    이름 글자로 탈퇴를 판단하면 안 됨: 누구나 닉네임을 "탈퇴한 작가"로 지을 수 있음 (D-95)
    """
    return WITHDRAWN if nickname is None else nickname


def get_or_create_google_user(db: Session, google_user_id: str, email: str | None = None) -> User:
    """구글 계정으로 처음 온 사람이면 유저를 만듦 (닉네임은 아직 비어 있음, D-48)

    google_user_id = 구글이 주는 사람 고유 번호(sub). 이메일이 바뀌어도 그대로라 이걸 기준으로 함
    이메일은 공지·출판 동의 요청용 — 구글에서 바꿨을 수 있으니 올 때마다 최신 값으로 갱신
    """
    user = db.scalar(
        select(User).where(
            User.provider == GOOGLE,
            User.provider_user_id == google_user_id,
            # 탈퇴한 껍데기는 찾지 않음 → 같은 구글 계정으로 다시 오면 새 계정
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        user = User(provider=GOOGLE, provider_user_id=google_user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif email is not None and user.email != email:
        # 구글에서 주소를 바꾼 사람 → 죽은 주소로 공지가 가지 않게
        user.email = email
        db.commit()
    return user


def withdraw(db: Session, user: User) -> None:
    """탈퇴 (6-4)

    쓴 문장은 남긴다 — 남이 그 뒤에 이어 쓴 이야기가 무너지기 때문 (D-06·D-92와 같은 이유)
    대신 **누구였는지 알 수 없게** 만든다: 구글 연결을 끊고, 닉네임을 비우고, 로그인을 막는다
    """
    # 구글 고유번호를 지우면 같은 계정으로 다시 와도 이 줄을 찾지 못함 (다른 사람 번호와 겹치지도 않게)
    user.provider_user_id = f"deleted-{uuid4().hex}"
    # 닉네임을 비우면 다른 사람이 그 이름을 쓸 수 있게 되고, 글에는 "탈퇴한 작가"로 보임
    user.nickname = None
    user.nickname_changed_at = None
    # 공지·동의 요청에 쓰던 주소도 함께 지움 (더는 연락할 일이 없음)
    user.email = None
    user.deleted_at = datetime.now(UTC)
    db.commit()
