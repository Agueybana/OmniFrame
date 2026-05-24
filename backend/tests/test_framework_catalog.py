from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.frameworks import load_framework_catalog

CATALOG_PATH = Path(__file__).resolve().parents[1] / "app" / "data" / "framework_catalog.json"
REQUIRED_COMPONENT_KEYS = {"id", "label", "description", "prompt", "questions"}


@pytest.fixture(autouse=True)
def clear_catalog_cache():
    load_framework_catalog.cache_clear()
    yield
    load_framework_catalog.cache_clear()


def test_framework_catalog_json_is_valid():
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)
    assert isinstance(catalog, list)
    assert len(catalog) == 50


def test_every_framework_has_valid_components():
    catalog = load_framework_catalog()

    for framework in catalog:
        assert "components" in framework, framework["id"]
        components = framework["components"]
        assert isinstance(components, list)
        assert len(components) >= 1, framework["id"]

        seen_ids: set[str] = set()
        for component in components:
            assert REQUIRED_COMPONENT_KEYS.issubset(component), (
                f"{framework['id']} missing keys in {component.get('id', component)}"
            )
            assert component["id"] not in seen_ids, f"{framework['id']} duplicate id {component['id']}"
            seen_ids.add(component["id"])

            assert isinstance(component["questions"], list)
            assert 3 <= len(component["questions"]) <= 5, framework["id"]
            assert all(isinstance(question, str) and question.strip() for question in component["questions"])
            assert component["description"].strip()
            assert component["prompt"].strip()
            assert component["label"].strip()


def test_framework_catalog_api_exposes_components():
    client = TestClient(app)
    response = client.get("/api/frameworks")
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 50
    swot = next(item for item in payload if item["id"] == "swot")
    assert len(swot["components"]) == 4
    assert swot["components"][0]["id"] == "strengths"
