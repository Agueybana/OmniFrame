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


def test_model_options_endpoint():
    client = TestClient(app)
    response = client.get("/api/model-options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["default"]["provider"] == "openai"
    assert any(provider["id"] == "google" for provider in payload["providers"])


def test_option_refresh_keeps_metric_domain(monkeypatch):
    monkeypatch.setenv("OMNIFRAME_USE_LLM", "false")
    client = TestClient(app)
    response = client.post(
        "/api/options/refresh",
        json={
            "goal": "Find a girlfriend in North Carolina around ages 33-39 who wants to have a child.",
            "framework_id": "swot",
            "focus_title": "Weaknesses: A vague desire to find a girlfriend can create mismatched dating choices.",
            "panel_title": "Watch metric",
            "panel_kind": "metric",
            "panel_prompt": "Select the metric that should prove this insight mattered.",
            "existing_options": ["Use specific examples without sarcasm."],
        },
    )

    assert response.status_code == 200
    options = " ".join(response.json()["option_sets"][0]).lower()
    assert "observable change" in options
    assert "sarcasm" not in options


def test_option_refresh_round_rotates_fallback_sets(monkeypatch):
    monkeypatch.setenv("OMNIFRAME_USE_LLM", "false")
    client = TestClient(app)
    payload = {
        "goal": "Rank features for a local events app.",
        "framework_id": "rice",
        "focus_title": "Reach evidence for daily event ingestion",
        "panel_title": "Reach evidence",
        "panel_kind": "evidence",
        "panel_prompt": "Choose what should justify the reach estimate.",
    }

    first = client.post("/api/options/refresh", json={**payload, "refresh_round": 0}).json()["option_sets"][0][0]
    second = client.post("/api/options/refresh", json={**payload, "refresh_round": 1}).json()["option_sets"][0][0]

    assert first != second
