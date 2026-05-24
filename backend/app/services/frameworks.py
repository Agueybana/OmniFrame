from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "framework_catalog.json"
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

    for item in catalog:
        item["active"] = item["id"] in ACTIVE_FRAMEWORK_IDS
    return catalog


def get_framework(framework_id: str) -> dict[str, Any] | None:
    return next((item for item in load_framework_catalog() if item["id"] == framework_id), None)
