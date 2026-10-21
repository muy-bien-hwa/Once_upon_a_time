from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_docs_live_under_api():
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    # /docs는 화면(SPA)이 받아 "없는 주소" 화면을 보여줌 → API 문서가 아니면 됨
    assert "swagger" not in client.get("/docs").text.lower()
