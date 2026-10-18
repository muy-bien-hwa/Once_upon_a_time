"""신고 처리 도구 (F-10, D-19·D-93)"""

import argparse
import unicodedata
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ForumComment, ForumPost, Report, Sentence, Story, User
from app.timeutil import KST

# 종류마다 (표, 신고 칸) — 문장·글·댓글을 같은 방식으로 다루기 위한 짝
TARGETS = {
    "문장": (Sentence, Report.sentence_id),
    "글": (ForumPost, Report.post_id),
    "댓글": (ForumComment, Report.comment_id),
}
# 영어로 쳐도 되게 (sentence·post·comment)
ALIASES = {"sentence": "문장", "post": "글", "comment": "댓글"}

REASON_LABELS = {
    "abuse": "욕설·비방",
    "sexual": "음란·선정성",
    "violence": "폭력·잔혹",
    "spam": "광고·도배",
    "privacy": "개인정보 노출",
    "plagiarism": "표절",
    "other": "기타",
}

STATUS_LABELS = {
    "active": "보임",
    "folded": "접힘",
    "deleted": "삭제",
    "removed": "숨김",
}


def kind_of(name: str) -> str:
    """'sentence'처럼 영어로 적어도 '문장'으로 바꿔 줌"""
    kind = ALIASES.get(name.lower(), name)
    if kind not in TARGETS:
        raise SystemExit(f"종류는 문장·글·댓글 중 하나여야 해요 (받은 값: {name})")
    return kind


def body_of(kind: str, row) -> str:
    """화면에 보여줄 내용 (글은 제목 + 본문)"""
    if kind == "문장":
        return row.content
    if kind == "글":
        return f"{row.title}\n{row.body}"
    return row.body


def pad(text: str, width: int) -> str:
    """표가 삐뚤어지지 않게 자리 맞추기 (한글은 터미널에서 두 칸을 차지함)"""
    used = sum(2 if unicodedata.east_asian_width(letter) in "WF" else 1 for letter in text)
    return text + " " * max(width - used, 0)


def shorten(text: str, width: int = 40) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= width else flat[: width - 1] + "…"


def when(moment: datetime) -> str:
    """한국 시간으로 (DB에는 UTC로 저장, docs 05)"""
    return moment.astimezone(KST).strftime("%Y-%m-%d %H:%M")


def report_counts(db: Session, kind: str):
    """그 종류에서 신고가 1건이라도 있는 대상 (신고 많은 순 → 최근 순)"""
    model, column = TARGETS[kind]
    count = func.count(Report.id)
    latest = func.max(Report.created_at)
    rows = db.execute(
        select(model, User.nickname, count, latest)
        .join(User, User.id == model.author_id)
        .join(Report, column == model.id)
        .group_by(model.id, User.nickname)
        .order_by(count.desc(), latest.desc())
    ).all()
    return [(kind, row, nickname, number, last) for row, nickname, number, last in rows]


def show_list(db: Session, kinds: list[str], limit: int) -> None:
    piled = [item for kind in kinds for item in report_counts(db, kind)]
    # 종류가 섞여 있어도 신고가 많은 것부터
    piled.sort(key=lambda item: (item[3], item[4]), reverse=True)

    if not piled:
        print("신고가 쌓인 글이 없어요.")
        return

    print(
        f"{pad('종류', 6)}{'번호':>6}{'신고':>6}  {pad('상태', 6)}{pad('쓴 사람', 14)}"
        f"{pad('마지막 신고', 18)}내용"
    )
    for kind, row, nickname, number, last in piled[:limit]:
        status = STATUS_LABELS.get(row.status, row.status)
        print(
            f"{pad(kind, 6)}{row.id:>6}{number:>6}  {pad(status, 6)}{pad(nickname, 14)}"
            f"{pad(when(last), 18)}{shorten(body_of(kind, row))}"
        )
    if len(piled) > limit:
        print(f"... 그 밖에 {len(piled) - limit}개 더 (--limit 으로 늘릴 수 있어요)")


def find(db: Session, kind: str, target_id: int):
    model, _ = TARGETS[kind]
    row = db.get(model, target_id)
    if row is None:
        raise SystemExit(f"{kind} {target_id}번을 찾을 수 없어요.")
    return row


def describe(db: Session, kind: str, row) -> None:
    """대상 한 건의 정보 (바꾸기 전에도 이걸 먼저 보여줌)"""
    author = db.get(User, row.author_id)
    _, column = TARGETS[kind]
    number = db.scalar(select(func.count()).select_from(Report).where(column == row.id))

    print(
        f"[{kind} {row.id}번] 상태: {STATUS_LABELS.get(row.status, row.status)} · 신고 {number}건"
    )
    print(f"쓴 사람: {author.nickname} (유저 {author.id}번) · 쓴 때: {when(row.created_at)}")
    print(f"어디: {where_of(db, kind, row)}")
    print("-" * 60)
    print(body_of(kind, row))
    print("-" * 60)


def where_of(db: Session, kind: str, row) -> str:
    """이 글이 어디에 있는지 (스토리·글 번호) → 앱에서 찾아보기 좋게"""
    if kind == "문장":
        story = db.get(Story, row.story_id)
        return f"스토리 {story.id}번 '{story.title}' · 주소 /s/{row.id}"
    if kind == "글":
        return f"스토리 {row.story_id}번 커뮤니티 · 주소 /forum/posts/{row.id}"
    post = db.get(ForumPost, row.post_id)
    return f"커뮤니티 글 {post.id}번 '{post.title}' · 주소 /forum/posts/{post.id}"


def show_one(db: Session, kind: str, target_id: int) -> None:
    row = find(db, kind, target_id)
    describe(db, kind, row)

    _, column = TARGETS[kind]
    reports = db.execute(
        select(Report, User.nickname)
        .join(User, User.id == Report.reporter_id)
        .where(column == row.id)
        .order_by(Report.created_at)
    ).all()
    if not reports:
        print("신고 내역이 없어요.")
        return

    print(f"신고 {len(reports)}건:")
    for report, nickname in reports:
        reason = REASON_LABELS.get(report.reason, report.reason)
        print(f"  · {when(report.created_at)} {nickname} — {reason}")
        if report.detail:
            print(f"    “{report.detail}”")


def confirm(question: str) -> bool:
    answer = input(f"{question} (y/N) ").strip().lower()
    return answer in ("y", "yes")


def change(db: Session, kind: str, target_id: int, action: str) -> None:
    """fold·unfold·hide 공통: 보여주고 → 묻고 → 바꿈"""
    row = find(db, kind, target_id)
    describe(db, kind, row)

    status, question, done = PLANS[action]
    if kind == "문장" and action == "hide" and row.parent_id is None:
        print("※ 이 문장은 스토리의 첫 문장이라, 숨기면 스토리가 목록에서 통째로 사라져요.")
    if row.status == status and action != "unfold":
        print(f"이미 {STATUS_LABELS[status]} 상태예요.")
        return
    if not confirm(question):
        print("그만뒀어요.")
        return

    row.status = status
    if action == "unfold":
        # 신고를 비워야 다시 쌓일 때까지 또 접히지 않음 (D-93)
        _, column = TARGETS[kind]
        cleared = db.execute(delete(Report).where(column == row.id)).rowcount
        print(f"신고 {cleared}건을 지웠어요.")
    db.commit()
    print(done)


PLANS = {
    "unfold": ("active", "되돌릴까요? (다시 보이고 신고 기록이 지워집니다)", "다시 보이게 했어요."),
    "fold": ("folded", "가릴까요? (내용이 '신고 처리된 …'으로 바뀝니다)", "가렸어요."),
    "hide": ("removed", "완전히 숨길까요? (목록에서 사라집니다)", "숨겼어요."),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="신고 처리 도구 (PM용)")
    commands = parser.add_subparsers(dest="command", required=True)

    listing = commands.add_parser("list", help="신고가 쌓인 순서로 보기")
    listing.add_argument("--kind", help="문장·글·댓글 중 하나만 보기")
    listing.add_argument("--limit", type=int, default=20, help="몇 개까지 보여줄지 (기본 20)")

    for name, help_text in (
        ("show", "내용과 신고 내역 보기"),
        ("unfold", "되돌리기 (다시 보이게 + 신고 비우기)"),
        ("fold", "바로 가리기"),
        ("hide", "완전히 숨기기"),
    ):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("kind", help="문장·글·댓글")
        sub.add_argument("id", type=int, help="번호")

    args = parser.parse_args()

    with SessionLocal() as db:
        if args.command == "list":
            kinds = [kind_of(args.kind)] if args.kind else list(TARGETS)
            show_list(db, kinds, args.limit)
        elif args.command == "show":
            show_one(db, kind_of(args.kind), args.id)
        else:
            change(db, kind_of(args.kind), args.id, args.command)


if __name__ == "__main__":
    main()
