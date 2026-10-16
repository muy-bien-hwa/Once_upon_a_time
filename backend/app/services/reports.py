"""신고·자동 접기 (F-10, D-13·D-49·D-82·D-93)

- 1인 1회 (DB UNIQUE로 막음) · 자기 글은 신고 불가 · 접힘·삭제된 대상은 신고 불가
- 신고가 기준(기본 5건) 이상 쌓이면 **같은 처리 안에서** 바로 접힘(folded)
- 문장·커뮤니티 글·댓글이 같은 표(reports)를 씀 → 규칙도 한곳에서
- 접힘을 되돌리는 일은 PM이 직접 (운영 도구, D-19)
"""

from sqlalchemy import and_, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import InstrumentedAttribute, Session, aliased

from app.config import settings
from app.errors import api_error
from app.models import ForumComment, ForumPost, Report, Sentence, User
from app.schemas.report import ReportCreate
from app.services.forum import post_gone
from app.services.forum_comments import comment_gone, readable_post
from app.services.stories import find_visible_story

_root = aliased(Sentence)


def report_sentence(db: Session, user: User, sentence_id: int, data: ReportCreate) -> None:
    """문장 신고 (#31)"""
    _check_detail(data)
    # 스토리째 숨겨졌으면(첫 문장이 removed) 그 안의 문장도 없는 것으로 봄 (투표와 같은 기준)
    # 세는 동안 다른 신고가 끼어들지 못하게 문장 줄을 잠그고 읽음
    sentence = db.scalar(
        select(Sentence)
        .join(_root, and_(_root.story_id == Sentence.story_id, _root.parent_id.is_(None)))
        .where(Sentence.id == sentence_id, _root.status != "removed")
        .with_for_update(of=Sentence)
    )
    if sentence is None or sentence.status == "removed":
        raise api_error(404, "SENTENCE_NOT_FOUND", "없거나 사라진 문장이에요")
    _check_target(sentence, user, "문장")
    _save(db, user, sentence, Report.sentence_id, data, "문장")


def report_post(db: Session, user: User, post_id: int, data: ReportCreate) -> None:
    """커뮤니티 글 신고 (#32)"""
    _check_detail(data)
    post = db.scalar(select(ForumPost).where(ForumPost.id == post_id).with_for_update())
    if post is None or post.status == "removed":
        raise post_gone(db, post_id)
    find_visible_story(db, post.story_id)
    _check_target(post, user, "글")
    _save(db, user, post, Report.post_id, data, "글")


def report_comment(db: Session, user: User, comment_id: int, data: ReportCreate) -> None:
    """댓글 신고 (#33)"""
    _check_detail(data)
    comment = db.scalar(select(ForumComment).where(ForumComment.id == comment_id).with_for_update())
    if comment is None or comment.status == "removed":
        raise comment_gone(db, comment_id)
    # 글이 지워졌거나 스토리가 숨겨졌으면 그 안의 댓글도 보이지 않음
    readable_post(db, comment.post_id)
    _check_target(comment, user, "댓글")
    _save(db, user, comment, Report.comment_id, data, "댓글")


def _check_detail(data: ReportCreate) -> None:
    """ "기타"는 무엇이 문제인지 알 수 없으므로 설명을 받음 (D-93)"""
    if data.reason == "other" and not data.detail:
        raise api_error(400, "REPORT_DETAIL_REQUIRED", "'기타'를 고르면 이유를 적어 주세요")


def _check_target(target: Sentence | ForumPost | ForumComment, user: User, label: str) -> None:
    """신고할 수 있는 대상인지 (내용이 가려졌으면 409 / 자기 것이면 403)"""
    if target.status != "active":
        # 이미 가려진 내용에는 신고도 하지 않음 (투표와 같은 이유, D-82)
        raise api_error(409, "REPORT_NOT_ALLOWED", f"지금은 신고할 수 없는 {label}이에요")
    if target.author_id == user.id:
        raise api_error(403, "SELF_REPORT", f"자기 {label}은 신고할 수 없어요")


def _save(
    db: Session,
    user: User,
    target: Sentence | ForumPost | ForumComment,
    column: InstrumentedAttribute,
    data: ReportCreate,
    label: str,
) -> None:
    """신고를 저장하고, 기준만큼 쌓였으면 같은 처리 안에서 접음

    column = Report.sentence_id · Report.post_id · Report.comment_id 중 하나
    """
    # 같은 사람이 두 번 보내도 DB가 거부 (UNIQUE) → 오류로 터지지 않게 "있으면 넘어가기"로 넣고
    # 새로 들어갔는지(id가 돌아왔는지)로 중복을 판단
    saved = db.scalar(
        insert(Report)
        .values(
            reporter_id=user.id,
            reason=data.reason,
            detail=data.detail,
            **{column.key: target.id},
        )
        .on_conflict_do_nothing(index_elements=[column, Report.reporter_id])
        .returning(Report.id)
    )
    if saved is None:
        raise api_error(409, "ALREADY_REPORTED", f"이미 신고한 {label}이에요")

    count = db.scalar(select(func.count()).select_from(Report).where(column == target.id))
    if count >= settings.reports_to_fold:
        # 내용을 가림 → 목록·화면에서 "신고 처리된 ..."만 보이고 그 뒤에 이어 쓸 수 없음 (D-69·D-70)
        target.status = "folded"
    db.commit()
