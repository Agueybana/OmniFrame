from __future__ import annotations

import hashlib
import json
from typing import Any


def _normalize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: _normalize_payload(payload[key]) for key in sorted(payload)}
    if isinstance(payload, list):
        return [_normalize_payload(item) for item in payload]
    if isinstance(payload, str):
        return payload.strip()
    return payload


def compute_input_fingerprint(
    *,
    goal: str,
    resources: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    details: str = "",
) -> str:
    normalized = {
        "goal": goal.strip(),
        "details": (details or "").strip(),
        "resources": _normalize_payload(resources),
        "answers": _normalize_payload(answers),
    }
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
