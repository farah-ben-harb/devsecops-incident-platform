def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_dashboard_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DevSecOps Incident Platform" in response.text
    assert "Create a new incident" in response.text


def test_ready_endpoint(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "reachable"}
