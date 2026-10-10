from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_overview_endpoint_returns_metrics() -> None:
    response = client.get("/api/overview")
    assert response.status_code == 200
    payload = response.json()
    assert "total_documents" in payload
    assert "total_chunks" in payload
    assert "questions_answered" in payload
