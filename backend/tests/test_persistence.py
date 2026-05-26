from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.models import Base
from backend.app.main import app
from backend.app.routers import persistence as persistence_router
from backend.app.services.input_fingerprint import compute_input_fingerprint


@pytest.fixture
def sqlite_session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def client(sqlite_session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DATABASE_URL", "sqlite://")

    def override_db_session() -> Generator[Session, None, None]:
        db = sqlite_session_factory()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(persistence_router, "is_database_configured", lambda: True)
    app.dependency_overrides[persistence_router.db_session] = override_db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_compute_input_fingerprint_is_stable():
    first = compute_input_fingerprint(
        goal="Build a roadmap",
        resources=[{"title": "Spec", "kind": "note"}],
        answers=[{"framework_id": "rice", "component_id": "reach", "question_index": 0, "answer": "1000 users"}],
    )
    second = compute_input_fingerprint(
        goal="Build a roadmap",
        resources=[{"title": "Spec", "kind": "note"}],
        answers=[{"framework_id": "rice", "component_id": "reach", "question_index": 0, "answer": "1000 users"}],
    )
    assert first == second
    assert len(first) == 64


def test_health_reports_db_status(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["db"] == "unavailable"


def test_profile_upsert_is_idempotent(client: TestClient):
    profile_id = str(uuid.uuid4())
    first = client.put(f"/api/profiles/{profile_id}", json={"display_name": "Analyst"})
    second = client.put(f"/api/profiles/{profile_id}", json={"display_name": "Analyst"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_profile_and_project_crud(client: TestClient):
    profile_id = str(uuid.uuid4())
    response = client.put(f"/api/profiles/{profile_id}", json={"display_name": "Analyst"})
    assert response.status_code == 200
    assert response.json()["display_name"] == "Analyst"

    create_response = client.post(
        f"/api/profiles/{profile_id}/projects",
        headers={"X-OmniFrame-Profile-Id": profile_id},
        json={"title": "Roadmap", "goal": "Prioritize AI features", "framework_id": "rice"},
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    other_profile = str(uuid.uuid4())
    forbidden = client.get(f"/api/projects/{project_id}", headers={"X-OmniFrame-Profile-Id": other_profile})
    assert forbidden.status_code == 404


def test_answer_bulk_upsert_is_idempotent(client: TestClient):
    profile_id = str(uuid.uuid4())
    client.put(f"/api/profiles/{profile_id}", json={})
    project = client.post(
        f"/api/profiles/{profile_id}/projects",
        headers={"X-OmniFrame-Profile-Id": profile_id},
        json={"title": "SWOT", "goal": "Assess launch readiness"},
    ).json()
    project_id = project["id"]
    headers = {"X-OmniFrame-Profile-Id": profile_id}
    payload = {
        "answers": [
            {
                "framework_id": "swot",
                "component_id": "strengths",
                "question_index": 0,
                "answer": "Strong engineering team",
            }
        ]
    }
    first = client.put(f"/api/projects/{project_id}/answers", headers=headers, json=payload)
    second = client.put(f"/api/projects/{project_id}/answers", headers=headers, json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()[0]["id"] == second.json()[0]["id"]
    assert second.json()[0]["answer"] == "Strong engineering team"


def test_score_upsert_marks_stale_scores(client: TestClient):
    profile_id = str(uuid.uuid4())
    client.put(f"/api/profiles/{profile_id}", json={})
    project = client.post(
        f"/api/profiles/{profile_id}/projects",
        headers={"X-OmniFrame-Profile-Id": profile_id},
        json={"title": "RICE", "goal": "Rank features"},
    ).json()
    project_id = project["id"]
    headers = {"X-OmniFrame-Profile-Id": profile_id}
    client.patch(
        f"/api/projects/{project_id}",
        headers=headers,
        json={"input_fingerprint": "old-fingerprint-value-12345678901234567890123456789012"},
    )

    old_score_payload = {
        "framework_id": "rice",
        "element_key": "feature-a",
        "element_kind": "row",
        "score": {"reach": 100, "impact": 2, "confidence": 80, "effort": 3},
        "content": {"title": "Feature A"},
        "input_fingerprint": "old-fingerprint-value-12345678901234567890123456789012",
    }
    client.put(f"/api/projects/{project_id}/scores", headers=headers, json=old_score_payload)

    new_score_payload = {
        "framework_id": "rice",
        "element_key": "feature-b",
        "element_kind": "row",
        "score": {"reach": 200, "impact": 3, "confidence": 70, "effort": 2},
        "content": {"title": "Feature B"},
        "input_fingerprint": "new-fingerprint-value-12345678901234567890123456789012",
        "mark_stale_on_fingerprint_change": True,
    }
    client.put(f"/api/projects/{project_id}/scores", headers=headers, json=new_score_payload)

    scores = client.get(f"/api/projects/{project_id}/scores", headers=headers).json()
    stale = next(item for item in scores if item["element_key"] == "feature-a")
    fresh = next(item for item in scores if item["element_key"] == "feature-b")
    assert stale["is_stale"] is True
    assert fresh["is_stale"] is False


def _make_swot_project(client: TestClient, *, details: str | None = None) -> tuple[str, dict]:
    profile_id = str(uuid.uuid4())
    client.put(f"/api/profiles/{profile_id}", json={})
    headers = {"X-OmniFrame-Profile-Id": profile_id}
    payload = {"title": "SWOT", "goal": "Assess launch readiness", "framework_id": "swot"}
    if details is not None:
        payload["details"] = details
    project = client.post(f"/api/profiles/{profile_id}/projects", headers=headers, json=payload).json()
    return project["id"], headers


def test_project_details_round_trips(client: TestClient):
    project_id, headers = _make_swot_project(client, details="# Details\nfirst version")
    created = client.get(f"/api/projects/{project_id}", headers=headers).json()
    assert created["details"] == "# Details\nfirst version"

    updated = client.patch(f"/api/projects/{project_id}", headers=headers, json={"details": "second version"}).json()
    assert updated["details"] == "second version"
    assert client.get(f"/api/projects/{project_id}", headers=headers).json()["details"] == "second version"


def test_component_result_generates_caches_and_regenerates(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    calls = {"n": 0}

    async def fake_generate(framework_id, component, project_details, goal, provider=None, model_id=None):
        calls["n"] += 1
        return f"GEN[{component['id']}|{(project_details or goal)[:12]}]#{calls['n']}"

    monkeypatch.setattr(persistence_router, "generate_component_result", fake_generate)

    project_id, headers = _make_swot_project(client, details="Rich details v1")

    first = client.post(
        f"/api/projects/{project_id}/components/strengths/result",
        headers=headers,
        json={"framework_id": "swot"},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["component_id"] == "strengths"
    assert body["text"].startswith("GEN[strengths")
    assert body["is_stale"] is False
    assert calls["n"] == 1

    # Cached read (no regenerate) returns the same text without another LLM call.
    cached = client.post(
        f"/api/projects/{project_id}/components/strengths/result",
        headers=headers,
        json={"framework_id": "swot"},
    )
    assert cached.status_code == 200
    assert cached.json()["text"] == body["text"]
    assert calls["n"] == 1

    listed = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert [row["component_id"] for row in listed] == ["strengths"]
    assert listed[0]["is_stale"] is False

    # Editing Project Details flags the cached result stale on read (no regeneration yet).
    client.patch(f"/api/projects/{project_id}", headers=headers, json={"details": "Rich details v2 changed"})
    stale = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert stale[0]["is_stale"] is True
    assert calls["n"] == 1

    # Explicit regenerate recomputes and clears staleness.
    regen = client.post(
        f"/api/projects/{project_id}/components/strengths/result",
        headers=headers,
        json={"framework_id": "swot", "regenerate": True},
    )
    assert regen.status_code == 200
    assert regen.json()["is_stale"] is False
    assert calls["n"] == 2
    refreshed = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert refreshed[0]["is_stale"] is False


def test_component_result_unknown_component_returns_404(client: TestClient):
    project_id, headers = _make_swot_project(client)
    response = client.post(
        f"/api/projects/{project_id}/components/not_a_component/result",
        headers=headers,
        json={"framework_id": "swot"},
    )
    assert response.status_code == 404


def test_component_result_surfaces_llm_failure(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def boom(framework_id, component, project_details, goal, provider=None, model_id=None):
        raise RuntimeError("openai (gpt-5.1) request failed: 401 Unauthorized")

    monkeypatch.setattr(persistence_router, "generate_component_result", boom)
    project_id, headers = _make_swot_project(client)
    response = client.post(
        f"/api/projects/{project_id}/components/strengths/result",
        headers=headers,
        json={"framework_id": "swot"},
    )
    assert response.status_code == 502
    assert "401 Unauthorized" in response.json()["detail"]  # real reason surfaced, no description fallback
    # A failed generation is not persisted (so it won't be served as a fake success later).
    listed = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert listed == []


def test_project_details_chat_applies_and_persists(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_edit(current, instruction, goal, provider=None, model_id=None):
        return ("# Details\nBudget: $50k", f"Applied: {instruction[:12]}")

    monkeypatch.setattr(persistence_router, "apply_project_details_edit", fake_edit)
    project_id, headers = _make_swot_project(client)

    response = client.post(
        f"/api/projects/{project_id}/details/chat",
        headers=headers,
        json={"instruction": "add that our budget is $50k"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["details"] == "# Details\nBudget: $50k"
    assert body["summary"].startswith("Applied")

    persisted = client.get(f"/api/projects/{project_id}", headers=headers).json()
    assert persisted["details"] == "# Details\nBudget: $50k"


def test_project_details_chat_appends_when_llm_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def no_edit(current, instruction, goal, provider=None, model_id=None):
        return None

    monkeypatch.setattr(persistence_router, "apply_project_details_edit", no_edit)
    project_id, headers = _make_swot_project(client, details="Existing line")

    response = client.post(
        f"/api/projects/{project_id}/details/chat",
        headers=headers,
        json={"instruction": "remember the deadline is Q3"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "remember the deadline is Q3" in body["details"]
    assert "Existing line" in body["details"]
    assert "LLM unavailable" in body["summary"]


def test_project_details_chat_accepts_large_instruction(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_edit(current, instruction, goal, provider=None, model_id=None):
        return ("# Details\nmerged", "merged large note")

    monkeypatch.setattr(persistence_router, "apply_project_details_edit", fake_edit)
    project_id, headers = _make_swot_project(client)
    big = "# Heading\n" + ("- bullet line with some content\n" * 2000)  # ~60k chars, was rejected at 8k
    response = client.post(
        f"/api/projects/{project_id}/details/chat",
        headers=headers,
        json={"instruction": big},
    )
    assert response.status_code == 200


def test_project_details_import_assimilates_and_persists(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_assimilate(current, document, filename, goal, provider=None, model_id=None):
        return (f"{current}\n## From {filename}\nassimilated".strip(), f"Imported {filename}")

    monkeypatch.setattr(persistence_router, "assimilate_project_details", fake_assimilate)
    project_id, headers = _make_swot_project(client, details="Existing")
    response = client.post(
        f"/api/projects/{project_id}/details/import",
        headers=headers,
        json={"document": "# Spec\nlots of detail", "filename": "spec.md"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "assimilated" in body["details"]
    assert body["summary"] == "Imported spec.md"
    assert client.get(f"/api/projects/{project_id}", headers=headers).json()["details"] == body["details"]


def test_project_details_import_appends_when_llm_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def no_assimilate(current, document, filename, goal, provider=None, model_id=None):
        return None

    monkeypatch.setattr(persistence_router, "assimilate_project_details", no_assimilate)
    project_id, headers = _make_swot_project(client, details="Existing line")
    response = client.post(
        f"/api/projects/{project_id}/details/import",
        headers=headers,
        json={"document": "imported body text", "filename": "notes.txt"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "Existing line" in body["details"]
    assert "imported body text" in body["details"]
    assert "## Imported: notes.txt" in body["details"]
    assert "LLM unavailable" in body["summary"]


def test_component_result_goes_stale_after_details_chat(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    async def fake_generate(framework_id, component, project_details, goal, provider=None, model_id=None):
        return f"gen-{component['id']}"

    async def fake_edit(current, instruction, goal, provider=None, model_id=None):
        return (f"{current}\n{instruction}".strip(), "changed")

    monkeypatch.setattr(persistence_router, "generate_component_result", fake_generate)
    monkeypatch.setattr(persistence_router, "apply_project_details_edit", fake_edit)
    project_id, headers = _make_swot_project(client, details="v1")

    client.post(
        f"/api/projects/{project_id}/components/strengths/result",
        headers=headers,
        json={"framework_id": "swot"},
    )
    before = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert before[0]["is_stale"] is False

    client.post(f"/api/projects/{project_id}/details/chat", headers=headers, json={"instruction": "add a new constraint"})
    after = client.get(f"/api/projects/{project_id}/component-results?framework_id=swot", headers=headers).json()
    assert after[0]["is_stale"] is True
