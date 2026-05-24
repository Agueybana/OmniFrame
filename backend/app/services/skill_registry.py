from __future__ import annotations

from functools import lru_cache
from pathlib import Path


SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"


@lru_cache(maxsize=32)
def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=32)
def load_framework_skill(framework_id: str) -> str:
    path = SKILLS_DIR / "frameworks" / f"{framework_id}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def framework_skill_pack(framework_id: str) -> str:
    parts = [
        load_skill("domain_analyst"),
        load_skill("context_accumulator"),
        load_framework_skill(framework_id),
    ]
    return "\n\n".join(part for part in parts if part)
