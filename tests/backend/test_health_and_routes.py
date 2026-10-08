"""Backend test suite for FastAPI lifecycle, health check, CORS, and reserved routes."""

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.health import HealthResponse


client = TestClient(app)


def test_app_lifecycle_and_metadata() -> None:
    """Verify application starts and contains proper metadata."""
    assert app.title == "JalDrishti API"
    assert app.version == "0.1.0"
    assert app.description is not None


def test_health_endpoint_success() -> None:
    """Verify GET /health returns HTTP 200 with required schema."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "project" in data
    assert "version" in data

    assert data["status"] == "ok"
    assert data["project"] == "jaldrishti"
    assert data["version"] == "0.1.0"

    # Verify Pydantic schema validation
    parsed = HealthResponse(**data)
    assert parsed.status == "ok"
    assert parsed.project == "jaldrishti"
    assert parsed.version == "0.1.0"


def test_cors_headers() -> None:
    """Verify CORS headers are returned for configured frontend origin."""
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_rejects_unauthorized_origin() -> None:
    """Verify CORS headers are omitted for unauthorized origins."""
    response = client.get(
        "/health",
        headers={"Origin": "http://malicious-site.example.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


def test_live_restore_endpoint_returns_200() -> None:
    """Verify POST /restore returns HTTP 200 OK with live conservation roadmap."""
    response = client.post("/restore", json={})
    assert response.status_code == 200
    data = response.json()
    assert "prioritized_actions" in data
    assert "restoration_strategy" in data


def test_live_material_compatibility_endpoint_returns_200() -> None:
    """Verify POST /material-compatibility returns HTTP 200 OK with compatibility evaluation."""
    response = client.post("/material-compatibility", json={})
    assert response.status_code == 200
    data = response.json()
    assert "candidate_interventions" in data
    assert data.get("verification_required") is True
