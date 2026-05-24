from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_framework_catalog_marks_three_live_routes():
    client = TestClient(app)
    response = client.get("/api/frameworks")
    assert response.status_code == 200
    live = [item["id"] for item in response.json() if item["active"]]
    assert live == ["swot", "lean_startup", "okrs", "porters_five_forces", "pestle", "rice", "triz"]
