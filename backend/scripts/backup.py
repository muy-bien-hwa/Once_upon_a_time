"""운영 DB 백업 (PM용)

- 최신 1개만 두고 덮어씀 — 개인정보 처리방침 9조에 그렇게 적어 두었음
- 받다가 실패해도 지난 백업이 남도록, 새 파일로 받은 뒤 바꿔치기함
- 접속 문자열은 화면에 찍지 않음

    uv run python -m scripts.backup --url "postgresql://..."
    uv run python -m scripts.backup --url-file "%USERPROFILE%/.relaystory/db-url.txt"
    uv run python -m scripts.backup            # DATABASE_URL 환경변수에서 읽음

자동으로 돌릴 때는 --url-file 을 씁니다. 접속 문자열을 명령줄에 적으면
작업 스케줄러 화면과 실행 중인 프로그램 목록에 그대로 보이기 때문입니다.
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
# 접속이 안 되면 이만큼만 기다림 / 전체가 이보다 오래 걸리면 중단
CONNECT_SECONDS = 15
LIMIT_MINUTES = 20
# 자동으로 돌 때 결과를 적어 두는 곳 (사람 글은 안 들어감, 최근 20줄만)
LOG = HERE / "backups" / "last-runs.txt"
KEEP_LINES = 20

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
    parser.add_argument(
        "--url-file", type=Path, help="접속 문자열이 한 줄로 적힌 파일 (자동 실행용)"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT, help=f"받을 파일 (기본 {DEFAULT})")
    parser.add_argument("--pg-dump", help="pg_dump 경로를 직접 지정할 때")
    parser.add_argument(
        "--minutes",
        type=int,
        default=LIMIT_MINUTES,
        help=f"이보다 오래 걸리면 중단 (기본 {LIMIT_MINUTES}분)",
    )
    args = parser.parse_args()

    url = args.url or read_url_file(args.url_file) or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "접속 문자열이 없어요. --url 이나 --url-file 로 주거나 DATABASE_URL 을 설정해 주세요."
        )

    tool = args.pg_dump or find_pg_dump()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    working = args.out.with_suffix(args.out.suffix + ".new")

    print(f"받는 중… ({args.out.name})")
    started = time.perf_counter()
    try:
        done = subprocess.run(  # noqa: S603
            [
                tool,
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                # 저절로 돌 때는 물어볼 사람이 없음 → 비밀번호를 묻지 말고 그냥 실패하게
                "--no-password",
                f"--file={working}",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=args.minutes * 60,
            # 접속이 안 되는 곳에서 하염없이 기다리지 않게
            env={**os.environ, "PGCONNECT_TIMEOUT": str(CONNECT_SECONDS)},
        )
    except subprocess.TimeoutExpired:
        working.unlink(missing_ok=True)
        write_log(f"실패 — {args.minutes}분이 지나 중단함")
        raise SystemExit(
            f"{args.minutes}분이 지나도 안 끝나 중단했어요. 지난 백업은 그대로 둡니다."
        ) from None

    if done.returncode != 0:
        working.unlink(missing_ok=True)
        # 오류 글에 접속 문자열이 섞여 나올 수 있어 비밀번호 부분을 가림
        reason = hide_password(done.stderr.strip())
        print(reason, file=sys.stderr)
        last = reason.splitlines()[-1][:120] if reason else "까닭 모름"
        write_log(f"실패 — {last}")
        raise SystemExit("백업에 실패했어요. 지난 백업은 그대로 둡니다.")

    working.replace(args.out)
    size = args.out.stat().st_size / 1024 / 1024
    print(f"끝. {size:.1f}MB · {time.perf_counter() - started:.1f}초 · {args.out}")
    write_log(f"됨 — {size:.1f}MB · {time.perf_counter() - started:.1f}초")
    print("되돌릴 때: pg_restore --clean --if-exists --no-owner -d <접속 문자열> " + str(args.out))


def read_url_file(path: Path | None) -> str | None:
    """파일에 한 줄로 적어 둔 접속 문자열 (자동 실행용)"""
    if path is None:
        return None
    if not path.exists():
        raise SystemExit(f"접속 문자열 파일이 없어요: {path}")
    # utf-8-sig: 윈도우 메모장·Set-Content가 파일 맨 앞에 몰래 넣는 표식(BOM)을 떼어 냄
    # 안 떼면 pg_dump가 주소를 못 알아보고 엉뚱하게 내 컴퓨터의 DB에 붙으려 함
    text = path.read_text(encoding="utf-8-sig").strip()
    if text and not text.startswith("postgres"):
        raise SystemExit(f"접속 문자열 같지 않아요 ({path}) — postgresql:// 로 시작해야 합니다.")
    return text or None


def write_log(result: str) -> None:
    """언제 돌았고 어떻게 됐는지만 남김 → 자동 실행이 조용히 멈춰도 알 수 있게"""
    stamp = time.strftime("%Y-%m-%d %H:%M")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    lines = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    lines.append(f"{stamp}  {result}")
    LOG.write_text("\n".join(lines[-KEEP_LINES:]) + "\n", encoding="utf-8")


def hide_password(text: str) -> str:
    """오류 글에 섞인 비밀번호를 가림 (postgresql://이름:비밀번호@...)"""
    import re

    return re.sub(r"(postgresql://[^:/\s]+:)[^@\s]+", r"\1****", text)


if __name__ == "__main__":
    main()
