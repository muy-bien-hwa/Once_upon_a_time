"""배포 전 자기 점검 + 안전 규칙 헤더 (6-3 보안 점검)"""

import pytest

from app.config import settings
from app.safety import check_settings, docs_url

STRONG = "a" * 32


@pytest.fixture
def production(monkeypatch):
    """배포된 것처럼 (https로 서비스하는 상태) 설정만 바꿔 둠"""
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "backend_origin", "https://relaystory.kr")
    monkeypatch.setattr(settings, "google_client_id", "id")
    monkeypatch.setattr(settings.google_client_secret, "_secret_value", "secret", raising=False)


def set_secret(monkeypatch, value: str) -> None:
    from pydantic import SecretStr

    monkeypatch.setattr(settings, "jwt_secret", SecretStr(value))


def test_production_refuses_to_start_without_a_signing_secret(production, monkeypatch):
    set_secret(monkeypatch, "")

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        check_settings()


def test_production_refuses_a_short_secret(production, monkeypatch):
    """짧은 비밀값은 찍어 맞힐 수 있어서 로그인 표를 위조당함"""
    set_secret(monkeypatch, "짧다")

    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        check_settings()


def test_production_refuses_http_address(production, monkeypatch):
    set_secret(monkeypatch, STRONG)
    monkeypatch.setattr(settings, "backend_origin", "http://relaystory.kr")

    with pytest.raises(RuntimeError, match="BACKEND_ORIGIN"):
        check_settings()


def test_production_starts_when_everything_is_set(production, monkeypatch):
    set_secret(monkeypatch, STRONG)

    check_settings()


def test_development_only_warns(monkeypatch, caplog):
    """개발 PC에서는 막지 않고 알려 주기만 함"""
    monkeypatch.setattr(settings, "cookie_secure", False)
    set_secret(monkeypatch, "")

    check_settings()

    assert "배포 전에 채워야 함" in caplog.text


def test_responses_carry_the_safety_headers(client):
    headers = client.get("/api/health").headers

    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]
    assert "camera=()" in headers["Permissions-Policy"]


def test_api_docs_page_is_left_alone(client):
    """문서 화면은 스크립트를 CDN에서 받아 오므로 규칙에서 빼 둠"""
    assert "Content-Security-Policy" not in client.get("/api/docs").headers


def test_a_huge_request_is_refused(client):
    """거대한 요청 하나로 서버 메모리를 채우지 못하게"""
    response = client.post("/api/stories", json={"title": "제목", "content": "가" * 2_000_000})

    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "TOO_LARGE"


def test_api_docs_are_closed_in_production(monkeypatch):
    """배포에서는 API 문서 화면을 열지 않음 (구조를 통째로 보여 줄 이유가 없음)"""
    monkeypatch.setattr(settings, "cookie_secure", True)

    assert docs_url() is None


def test_api_docs_open_in_development(monkeypatch):
    monkeypatch.setattr(settings, "cookie_secure", False)

    assert docs_url() == "/api/docs"
