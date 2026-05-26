from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "framework_catalog.json"

# Frameworks with deterministic keyword routing and bespoke, hand-tuned generators.
# The router scores only these when auto-selecting a framework for a goal.
ACTIVE_FRAMEWORK_IDS = {
    "swot",
    "lean_startup",
    "okrs",
    "porters_five_forces",
    "pestle",
    "rice",
    "triz",
}


@lru_cache(maxsize=1)
def load_framework_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        catalog = json.load(handle)

    # Every catalog framework is user-selectable and generatable: the 7 in
    # ACTIVE_FRAMEWORK_IDS use bespoke generators, the rest fall back to the
    # catalog-driven generator (see canvas_generators.generate_from_catalog).
    for item in catalog:
        item["active"] = True
    return catalog


def selectable_framework_ids() -> set[str]:
    return {item["id"] for item in load_framework_catalog()}


def get_framework(framework_id: str) -> dict[str, Any] | None:
    return next((item for item in load_framework_catalog() if item["id"] == framework_id), None)
