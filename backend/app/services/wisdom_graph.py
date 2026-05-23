from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..models import FeedbackRequest


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "runtime"
EVENTS_PATH = RUNTIME_DIR / "wisdom_events.jsonl"


def store_feedback(payload: FeedbackRequest) -> str:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    event_id = str(uuid4())
    event = {
        "event_id": event_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload.model_dump(),
    }
    with EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")
    return event_id
