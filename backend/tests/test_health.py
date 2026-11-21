"""Unit tests for SchemeSaathi health check and core endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify that the /health endpoint responds with expected status structure."""
    with TestClient(app) as test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "SchemeSaathi"
        assert data["version"] == "0.1.0"
        assert "status" in data
        assert "indexed_documents_count" in data
        assert "embedding_model" in data
