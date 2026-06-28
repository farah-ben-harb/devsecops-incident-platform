def _payload():
    return {
        "title": "Database saturation on payments",
        "description": "Primary database is showing high latency for write queries.",
        "severity": "high",
        "status": "open",
        "service_name": "payments-api",
    }


def test_create_and_fetch_incident(client):
    create_response = client.post("/api/incidents", json=_payload())

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Database saturation on payments"
    assert created["severity"] == "high"

    fetch_response = client.get(f"/api/incidents/{created['id']}")

    assert fetch_response.status_code == 200
    assert fetch_response.json()["service_name"] == "payments-api"


def test_list_incidents_returns_created_records(client):
    client.post("/api/incidents", json=_payload())

    response = client.get("/api/incidents")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_incident(client):
    created = client.post("/api/incidents", json=_payload()).json()
    update_payload = {
        "title": "Database saturation mitigated",
        "description": "Traffic was shifted away from the hot partition.",
        "severity": "medium",
        "status": "mitigated",
        "service_name": "payments-api",
    }

    response = client.put(f"/api/incidents/{created['id']}", json=update_payload)

    assert response.status_code == 200
    assert response.json()["status"] == "mitigated"
    assert response.json()["title"] == "Database saturation mitigated"


def test_delete_incident(client):
    created = client.post("/api/incidents", json=_payload()).json()

    delete_response = client.delete(f"/api/incidents/{created['id']}")
    fetch_response = client.get(f"/api/incidents/{created['id']}")

    assert delete_response.status_code == 204
    assert fetch_response.status_code == 404


def test_validation_rejects_short_title(client):
    payload = _payload()
    payload["title"] = "no"

    response = client.post("/api/incidents", json=payload)

    assert response.status_code == 422


def test_metrics_exposes_custom_counters(client):
    client.post("/api/incidents", json=_payload())

    response = client.get("/metrics")

    assert response.status_code == 200
    assert "incident_created_total" in response.text
    assert "api_error_total" in response.text or "http_requests_total" in response.text
