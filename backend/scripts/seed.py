"""개발용 샘플 데이터 넣기

실행 (backend 폴더에서): uv run python -m scripts.seed
- 개발용 유저 2명이 없으면 만들고, 가짜 로그인에 쓸 id를 출력 → .env의 DEV_USER_ID에 적기
- 스토리가 하나도 없을 때만 샘플 스토리를 넣음 → 여러 번 실행해도 중복되지 않음
- --many: 목록 페이지 확인용 테스트 스토리 45개 추가 (이미 있으면 건너뜀)
- --hot: 홈 Hot 영역 확인용 가짜 추천·투표 추가 (3단계 전까지 Top 칸을 채워 보기 위한 개발용)
"""

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Sentence, SentenceVote, Story, StoryRecommendation, User
from app.timeutil import kst_today_start


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


def _today(hours: int) -> datetime:
    """오늘(한국 시간 0시 이후) 안의 시각 → 일간 순위에 잡히도록"""
    return max(_hours_ago(hours), kst_today_start() + timedelta(minutes=1))


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


MANY_COUNT = 45


def add_many_stories(db: Session, dev: User, writer: User) -> bool:
    """목록 페이지 확인용 (--many). "테스트 스토리 01"이 이미 있으면 넣지 않고 False"""
    if db.scalar(select(Story.id).where(Story.title == "테스트 스토리 01")):
        return False

    for i in range(1, MANY_COUNT + 1):
        creator, other = (dev, writer) if i % 2 else (writer, dev)
        # 7시간 간격 → 최근 것은 "n시간 전", 오래된 것은 날짜로 보임
        hours = i * 7
        title = f"테스트 스토리 {i:02d}"
        sentence = add_story(db, creator, title, f"목록 확인용 {i}번째 첫 문장이다.", hours)
        story = db.get(Story, sentence.story_id)
        # 깊이·작가 수가 스토리마다 다르도록 0~3문장을 이어 붙임
        for depth in range(i % 4):
            author = other if depth % 2 == 0 else creator
            content = f"{depth + 1}번째로 이어진 문장이다."
            sentence = add_sentence(
                db, story, author, content, sentence, hours_ago=hours - depth - 1
            )
    return True


READER_COUNT = 30


def add_hot_data(db: Session) -> bool:
    """홈 Hot 영역 확인용 가짜 추천·투표 (--hot). 추천이 이미 있으면 넣지 않고 False

    3단계에서 진짜 추천·투표 기능이 생기기 전까지 Top 칸을 채워 보기 위한 개발용 데이터
    """
    if db.scalar(select(func.count()).select_from(StoryRecommendation)) > 0:
        return False

    readers = [
        get_or_create_user(db, f"reader-{i:02d}", f"독자{i:02d}")
        for i in range(1, READER_COUNT + 1)
    ]
    stories = db.scalars(select(Story).order_by(Story.id).limit(14)).all()

    for index, story in enumerate(stories):
        reader_index = index
        # (언제, 몇 명이 추천) → 일간·주간·월간 순위가 서로 다르게 나오도록
        for when, amount in (
            (_today(2), index % 6 + 1),
            (_hours_ago(4 * 24), (index * 2) % 7),
            (_hours_ago(20 * 24), (index * 3) % 9),
        ):
            for _ in range(amount):
                db.add(
                    StoryRecommendation(
                        user_id=readers[reader_index % READER_COUNT].id,
                        story_id=story.id,
                        created_at=when,
                    )
                )
                reader_index += 1

        sentences = db.scalars(
            select(Sentence).where(Sentence.story_id == story.id, Sentence.status == "active")
        ).all()
        for order, sentence in enumerate(sentences):
            when = (_today(3), _hours_ago(3 * 24), _hours_ago(15 * 24))[order % 3]
            for _ in range((index + order) % 5 + 1):
                db.add(
                    SentenceVote(
                        user_id=readers[reader_index % READER_COUNT].id,
                        sentence_id=sentence.id,
                        value=1,
                        created_at=when,
                    )
                )
                reader_index += 1

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="개발용 샘플 데이터 넣기")
    parser.add_argument(
        "--many", action="store_true", help=f"목록 페이지 확인용 테스트 스토리 {MANY_COUNT}개 추가"
    )
    parser.add_argument("--hot", action="store_true", help="홈 Hot 영역 확인용 가짜 추천·투표 추가")
    args = parser.parse_args()

    with SessionLocal() as db:
        dev = get_or_create_user(db, "dev", "개발자")
        writer = get_or_create_user(db, "dev-2", "테스트작가")

        if db.scalar(select(func.count()).select_from(Story)) == 0:
            add_sample_stories(db, dev, writer)
            print("샘플 스토리 3개를 넣었어요.")
        else:
            print("스토리가 이미 있어서 샘플은 건너뛰었어요.")

        if args.many:
            if add_many_stories(db, dev, writer):
                print(f"테스트 스토리 {MANY_COUNT}개를 넣었어요.")
            else:
                print("테스트 스토리가 이미 있어서 건너뛰었어요.")

        if args.hot:
            if add_hot_data(db):
                print(f"Hot 확인용 가짜 추천·투표를 넣었어요 (독자 {READER_COUNT}명).")
            else:
                print("추천 기록이 이미 있어서 건너뛰었어요.")

        db.commit()
        print(f".env에 적을 값 → DEV_USER_ID={dev.id}  (닉네임: {dev.nickname})")


if __name__ == "__main__":
    main()
