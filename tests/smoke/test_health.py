"""Smoke test verifying FastAPI /health endpoint."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Verify GET /health returns HTTP 200 with required Phase 0 payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "ok",
        "project": "jaldrishti",
        "version": "0.1.0",
    }
