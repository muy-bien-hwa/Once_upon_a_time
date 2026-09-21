"""개발용 샘플 데이터 넣기

실행 (backend 폴더에서): uv run python -m scripts.seed
- 개발용 유저 2명이 없으면 만들고, 가짜 로그인에 쓸 id를 출력 → .env의 DEV_USER_ID에 적기
- 스토리가 하나도 없을 때만 샘플 스토리를 넣음 → 여러 번 실행해도 중복되지 않음
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Sentence, Story, User


def get_or_create_user(db: Session, provider_user_id: str, nickname: str) -> User:
    user = db.scalar(
        select(User).where(User.provider == "dev", User.provider_user_id == provider_user_id)
    )
    if user is None:
        user = User(provider="dev", provider_user_id=provider_user_id, nickname=nickname)
        db.add(user)
        db.flush()
    return user


def _hours_ago(hours: int) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


def add_sentence(
    db: Session,
    story: Story,
    author: User,
    content: str,
    parent: Sentence | None = None,
    status: str = "active",
    hours_ago: int = 0,
) -> Sentence:
    """parent가 없으면 첫 문장 → add_story에서만 사용 (스토리당 1개, D-65)"""
    sentence = Sentence(
        story_id=story.id,
        parent_id=parent.id if parent else None,
        author_id=author.id,
        content=content,
        depth=parent.depth + 1 if parent else 0,
        status=status,
        created_at=_hours_ago(hours_ago),
    )
    db.add(sentence)
    db.flush()
    return sentence


def add_story(db: Session, creator: User, title: str, content: str, hours_ago: int) -> Sentence:
    """스토리 = 제목 + 첫 문장 1개 (D-65). 첫 문장을 돌려줌"""
    story = Story(title=title, creator_id=creator.id, created_at=_hours_ago(hours_ago))
    db.add(story)
    db.flush()
    return add_sentence(db, story, creator, content, hours_ago=hours_ago)


def add_sample_stories(db: Session, dev: User, writer: User) -> None:
    # 스토리 1: 갈래, 접힌 문장, 삭제된 문장(아래에 이어진 문장 있음)을 모두 포함
    root = add_story(
        db, dev, "말하는 고양이", "옛날 옛적에 산골 마을에 말하는 고양이가 살았다.", 72
    )
    cat = db.get(Story, root.story_id)
    stars = add_sentence(
        db, cat, writer, "고양이는 매일 밤 지붕 위에서 별을 셌다.", root, hours_ago=60
    )
    add_sentence(db, cat, dev, "어느 날 밤, 별 하나가 사라졌다.", stars, hours_ago=48)
    add_sentence(db, cat, writer, "그러다 별 하나와 눈이 마주쳤다.", stars, hours_ago=5)
    doubt = add_sentence(
        db, cat, dev, "마을 사람들은 고양이의 말을 믿지 않았다.", root, hours_ago=50
    )
    folded = add_sentence(
        db, cat, writer, "접힘 예시: 신고가 쌓여 접힌 문장이다.", doubt, "folded", hours_ago=30
    )
    # 접히기 전에 달린 문장 → 접힌 문장 아래도 계속 읽을 수 있음 (D-70)
    add_sentence(db, cat, dev, "그래도 고양이는 포기하지 않았다.", folded, hours_ago=28)
    gone = add_sentence(
        db, cat, dev, "삭제 예시: 이 문장은 지워졌다.", doubt, "deleted", hours_ago=20
    )
    add_sentence(db, cat, writer, "그 뒤로 아무도 그 이야기를 꺼내지 않았다.", gone, hours_ago=10)

    # 스토리 2: 짧은 한 줄기
    first = add_story(db, writer, "비 오는 날의 편지", "편지는 늘 비 오는 날에만 도착했다.", 12)
    letter = db.get(Story, first.story_id)
    add_sentence(db, letter, dev, "오늘도 우체통이 젖어 있었다.", first, hours_ago=2)

    # 스토리 3: 첫 문장만 있음 → 막다른 문장 화면 예시
    add_story(db, writer, "바다 끝 등대지기", "옛날 옛적에 바다 끝에 등대지기가 살았다.", 24)


def main() -> None:
    with SessionLocal() as db:
        dev = get_or_create_user(db, "dev", "개발자")
        writer = get_or_create_user(db, "dev-2", "테스트작가")

        if db.scalar(select(func.count()).select_from(Story)) == 0:
            add_sample_stories(db, dev, writer)
            print("샘플 스토리 3개를 넣었어요.")
        else:
            print("스토리가 이미 있어서 샘플은 건너뛰었어요.")

        db.commit()
        print(f".env에 적을 값 → DEV_USER_ID={dev.id}  (닉네임: {dev.nickname})")


if __name__ == "__main__":
    main()
