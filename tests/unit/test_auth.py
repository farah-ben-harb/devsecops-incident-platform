import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core import security
from app.core.config import Settings
from app.main import app


def test_incident_api_rejects_missing_and_invalid_tokens():
    with TestClient(app) as client:
        missing = client.get("/api/incidents")
        invalid = client.get(
            "/api/incidents",
            headers={"Authorization": "Bearer not-the-test-token"},
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert "not-the-test-token" not in invalid.text


def test_unauthenticated_client_cannot_create_or_delete_incidents(client):
    payload = {
        "title": "Synthetic incident",
        "description": "Fictional test data only.",
        "severity": "low",
        "status": "open",
        "service_name": "test-service",
    }
    created = client.post("/api/incidents", json=payload).json()

    with TestClient(app) as unauthenticated_client:
        create_response = unauthenticated_client.post("/api/incidents", json=payload)
        delete_response = unauthenticated_client.delete(f"/api/incidents/{created['id']}")

    assert create_response.status_code == 401
    assert delete_response.status_code == 401
    assert client.get(f"/api/incidents/{created['id']}").status_code == 200


def test_incident_api_fails_closed_when_token_is_unconfigured(monkeypatch):
    monkeypatch.setattr(security, "get_settings", lambda: Settings(incident_api_token=None))

    with TestClient(app) as client:
        response = client.get("/api/incidents")

    assert response.status_code == 503
    assert "token" not in response.text.lower()


@pytest.mark.parametrize("environment", ["prod", "production"])
def test_production_rejects_the_local_example_token(environment):
    with pytest.raises(ValidationError):
        Settings(
            app_env=environment,
            incident_api_token="local-development-token-change-before-deploy",
        )
