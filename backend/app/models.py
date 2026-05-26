from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .services.frameworks import selectable_framework_ids


def _validate_framework_id(value: str | None) -> str | None:
    if value is None:
        return value
    if value not in selectable_framework_ids():
        raise ValueError(f"Unknown framework_id: {value}")
    return value


class GoalRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    goal: str = Field(..., min_length=8, max_length=20000)
    framework_id: str | None = Field(default=None, max_length=64)
    model_provider: Literal["openai", "google"] | None = None
    model_id: str | None = Field(default=None, max_length=120)

    _check_framework_id = field_validator("framework_id")(_validate_framework_id)


class RouteResponse(BaseModel):
    framework_id: str
    framework_name: str
    confidence: float = Field(..., ge=0, le=1)
    rationale: str
    selection_process: dict[str, Any] | None = None
    canvas: dict[str, Any]


class FeedbackRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    framework_id: str = Field(..., min_length=1, max_length=64)
    rating: int = Field(..., ge=1, le=5)
    outcome: Literal["clarified", "decided", "acted", "stalled"]
    comment: str | None = Field(default=None, max_length=1200)
    confidence: float | None = Field(default=None, ge=0, le=1)


class FeedbackResponse(BaseModel):
    event_id: str
    stored: bool


class OptionRefreshRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    goal: str = Field(..., min_length=1, max_length=20000)
    framework_id: str = Field(..., min_length=1, max_length=64)
    focus_title: str = Field(..., min_length=1, max_length=500)
    focus_description: str | None = Field(default=None, max_length=1200)
    panel_title: str = Field(..., min_length=1, max_length=160)
    panel_prompt: str | None = Field(default=None, max_length=800)
    panel_kind: str | None = Field(default=None, max_length=80)
    panel_value: str | None = Field(default=None, max_length=4000)
    existing_options: list[str] = Field(default_factory=list, max_length=60)
    refresh_round: int = Field(default=0, ge=0, le=1000)
    model_provider: Literal["openai", "google"] | None = None
    model_id: str | None = Field(default=None, max_length=120)

    _check_framework_id = field_validator("framework_id")(_validate_framework_id)


class OptionRefreshResponse(BaseModel):
    option_sets: list[list[str]]
