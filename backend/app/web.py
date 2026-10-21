"""빌드한 화면 내보내기 + 공유 미리보기 (D-81·F-05)

- 서버 하나가 API와 화면을 함께 내보냄 → 주소가 하나라 쿠키·CORS 문제가 없음
- `/s/{문장번호}`로 들어오면 그 문장 내용으로 공유 카드(카톡·트위터 미리보기)를 채움
- 빌드 결과물(`frontend/dist`)이 없으면 화면은 내보내지 않음 (개발 중에는 vite가 띄움)
"""

import logging
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import DbSession
from app.errors import api_error
from app.models import Sentence, Story

logger = logging.getLogger(__name__)

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
INDEX = DIST / "index.html"

# index.html의 이 두 줄 사이가 공유 카드 자리 → 문장 주소로 들어오면 서버가 갈아 끼움
SHARE_START = "<!--share-->"
SHARE_END = "<!--/share-->"

SITE_NAME = "옛날 옛적에"


def share_tags(title: str, description: str, url: str, kind: str = "website") -> str:
    """공유 카드에 들어갈 태그 (카톡·트위터가 이 태그를 읽어 미리보기를 만듦)"""
    title, description, url = (escape(value, quote=True) for value in (title, description, url))
    return (
        f"<title>{title}</title>"
        f'<meta property="og:site_name" content="{SITE_NAME}">'
        f'<meta property="og:type" content="{kind}">'
        f'<meta property="og:title" content="{title}">'
        f'<meta property="og:description" content="{description}">'
        f'<meta property="og:url" content="{url}">'
        f'<meta name="description" content="{description}">'
        f'<meta name="twitter:card" content="summary">'
    )


def tags_for(db: Session, path: str) -> str | None:
    """그 주소에 맞는 공유 카드. 문장 주소가 아니면 None (index.html의 기본 카드를 그대로 씀)"""
    number = path.removeprefix("s/")
    if not path.startswith("s/") or not number.isdigit():
        return None

    row = db.execute(
        select(Sentence.content, Sentence.status, Story.title)
        .join(Story, Story.id == Sentence.story_id)
        .where(Sentence.id == int(number))
    ).first()
    if row is None:
        return None

    content, status, title = row
    if status == "removed":
        return None
    # 가려진 문장의 내용은 공유 카드에도 쓰지 않음 (D-63·D-69)
    text = content if status == "active" else "지워졌거나 신고 처리된 문장이에요."
    return share_tags(
        f"{title} · {SITE_NAME}", text, f"{settings.backend_origin}/s/{number}", kind="article"
    )


def with_share_tags(html: str, tags: str | None) -> str:
    """index.html의 기본 카드 자리를 주어진 태그로 바꿈"""
    if tags is None or SHARE_START not in html or SHARE_END not in html:
        return html
    head, _, rest = html.partition(SHARE_START)
    _, _, tail = rest.partition(SHARE_END)
    return head + tags + tail


def mount(app: FastAPI) -> None:
    """화면 파일을 내보내는 주소들을 등록 (API 주소를 모두 등록한 **뒤에** 불러야 함)"""
    if not INDEX.exists():
        logger.info("frontend/dist가 없어 화면은 내보내지 않음 (개발 중에는 vite가 띄움)")
        return

    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False, response_model=None)
    def spa(path: str, db: DbSession) -> HTMLResponse | FileResponse:
        """어떤 주소로 들어와도 화면 파일 한 장을 보냄 (주소별 화면은 브라우저에서 React가 고름)"""
        if path.startswith(("api/", "auth/")):
            raise api_error(404, "NOT_FOUND", "없는 주소예요")

        # dist 안에 그 이름의 파일이 있으면 그대로 (robots.txt 같은 것)
        wanted = (DIST / path).resolve()
        if path and wanted.is_file() and DIST.resolve() in wanted.parents:
            return FileResponse(wanted)

        return HTMLResponse(with_share_tags(INDEX.read_text(encoding="utf-8"), tags_for(db, path)))
