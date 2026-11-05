"""운영 DB 백업 (PM용)

- 최신 1개만 두고 덮어씀 — 개인정보 처리방침 9조에 그렇게 적어 두었음
- 받다가 실패해도 지난 백업이 남도록, 새 파일로 받은 뒤 바꿔치기함
- 접속 문자열은 화면에 찍지 않음

    uv run python -m scripts.backup --url "postgresql://..."
    uv run python -m scripts.backup            # DATABASE_URL 환경변수에서 읽음
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# 기본 자리: backend/backups/relaystory.dump (깃에 올라가지 않게 .gitignore에 넣어 둠)
HERE = Path(__file__).resolve().parents[1]
DEFAULT = HERE / "backups" / "relaystory.dump"

# 윈도우에서 PATH에 없을 때 흔히 깔리는 자리
GUESSES = [Path(rf"C:\Program Files\PostgreSQL\{v}\bin\pg_dump.exe") for v in (18, 17, 16)]


def find_pg_dump() -> str:
    found = shutil.which("pg_dump")
    if found:
        return found
    for guess in GUESSES:
        if guess.exists():
            return str(guess)
    raise SystemExit(
        "pg_dump을 찾지 못했어요. PostgreSQL 설치 폴더의 bin을 PATH에 넣거나 "
        "--pg-dump 로 경로를 알려 주세요."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="운영 DB 백업 (최신 1개만 유지)")
    parser.add_argument("--url", help="접속 문자열 (없으면 DATABASE_URL 환경변수)")
    parser.add_argument("--out", type=Path, default=DEFAULT, help=f"받을 파일 (기본 {DEFAULT})")
    parser.add_argument("--pg-dump", help="pg_dump 경로를 직접 지정할 때")
    args = parser.parse_args()

    url = args.url or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("접속 문자열이 없어요. --url 로 주거나 DATABASE_URL 을 설정해 주세요.")

    tool = args.pg_dump or find_pg_dump()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    working = args.out.with_suffix(args.out.suffix + ".new")

    print(f"받는 중… ({args.out.name})")
    started = time.perf_counter()
    done = subprocess.run(  # noqa: S603
        [tool, "--format=custom", "--no-owner", "--no-privileges", f"--file={working}", url],
        capture_output=True,
        text=True,
    )
    if done.returncode != 0:
        working.unlink(missing_ok=True)
        # 오류 글에 접속 문자열이 섞여 나올 수 있어 비밀번호 부분을 가림
        print(hide_password(done.stderr.strip()), file=sys.stderr)
        raise SystemExit("백업에 실패했어요. 지난 백업은 그대로 둡니다.")

    working.replace(args.out)
    size = args.out.stat().st_size / 1024 / 1024
    print(f"끝. {size:.1f}MB · {time.perf_counter() - started:.1f}초 · {args.out}")
    print("되돌릴 때: pg_restore --clean --if-exists --no-owner -d <접속 문자열> " + str(args.out))


def hide_password(text: str) -> str:
    """오류 글에 섞인 비밀번호를 가림 (postgresql://이름:비밀번호@...)"""
    import re

    return re.sub(r"(postgresql://[^:/\s]+:)[^@\s]+", r"\1****", text)


if __name__ == "__main__":
    main()
