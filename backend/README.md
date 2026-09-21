# backend

Once upon a time API 서버 · FastAPI + PostgreSQL + SQLAlchemy + Alembic

## 구조
```
backend/
├─ app/
│  ├─ main.py         서버 시작점, API 주소 정의 (현재 /api/health)
│  ├─ config.py       .env를 읽어서 설정값으로 만듦 (DB 접속 정보 등)
│  ├─ db.py           DB 연결 관리자 (engine)
│  └─ models/         테이블 정의 (파이썬 클래스 1개 = 테이블 1개)
│     ├─ base.py      공통 부품: id, created_at, 제약조건 이름 규칙, status 값 규칙
│     ├─ user.py      users
│     ├─ story.py     stories, story_recommendations
│     ├─ sentence.py  sentences, sentence_votes
│     ├─ forum.py     forum_posts, forum_post_votes, forum_comments
│     ├─ report.py    reports
│     └─ __init__.py  모델 전체를 한곳에서 불러옴 (Alembic이 빠짐없이 인식하도록)
├─ migrations/        DB 구조 변경 이력 (Alembic)
│  ├─ env.py          Alembic 실행 설정, DB 주소를 app.config(.env)에서 가져옴
│  ├─ script.py.mako  새 마이그레이션 파일의 틀
│  └─ versions/       마이그레이션 파일
├─ tests/             자동 테스트 (pytest, DB relay_test 사용)
├─ alembic.ini        Alembic 설정
├─ pyproject.toml     프로젝트 정보 + 필요한 패키지 목록
├─ uv.lock            설치된 패키지의 정확한 버전
└─ .python-version    Python 3.13
```

## 실행
1. 패키지 설치: `uv sync`
2. `.env` 작성: DB 접속 정보 (항목은 `app/config.py` 참고)
3. PostgreSQL에 DB `relay` 만들기
4. 테이블 만들기: `uv run alembic upgrade head`
5. 서버 실행: `uv run fastapi dev app/main.py` → http://localhost:8000/docs

## 테스트 · 코드 검사
- 테스트: `uv run pytest` (PostgreSQL에 DB `relay_test` 필요)
- 코드 검사: `uv run ruff check .` / 정리: `uv run ruff format .`
