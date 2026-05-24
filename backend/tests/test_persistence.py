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
