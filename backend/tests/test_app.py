from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_docs_live_under_api():
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 404
