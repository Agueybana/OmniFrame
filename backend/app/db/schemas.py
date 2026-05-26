from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ProjectStatus = Literal["draft", "active", "archived"]
ResourceKind = Literal["link", "note", "file"]
ElementKind = Literal["section", "item", "row", "panel", "component"]


class ProfileUpsertRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)


class ProfileResponse(BaseModel):
    id: UUID
    display_name: str | None
    created_at: datetime
    updated_at: datetime


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    goal: str = Field(..., min_length=1, max_length=20000)
    details: str | None = Field(default=None, max_length=100000)
    framework_id: str | None = Field(default=None, max_length=64)
    status: ProjectStatus = "draft"


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    goal: str | None = Field(default=None, min_length=1, max_length=20000)
    details: str | None = Field(default=None, max_length=100000)
    framework_id: str | None = Field(default=None, max_length=64)
    status: ProjectStatus | None = None
    input_fingerprint: str | None = Field(default=None, max_length=128)


class ProjectResponse(BaseModel):
    id: UUID
    profile_id: UUID
    title: str
    goal: str
    details: str | None
    framework_id: str | None
    status: ProjectStatus
    input_fingerprint: str | None
    created_at: datetime
    updated_at: datetime


class ResourceCreateRequest(BaseModel):
    kind: ResourceKind
    title: str = Field(..., min_length=1, max_length=500)
    body: str | None = Field(default=None, max_length=20000)
    uri: str | None = Field(default=None, max_length=2000)


class ResourceUpdateRequest(BaseModel):
    kind: ResourceKind | None = None
    title: str | None = Field(default=None, min_length=1, max_length=500)
    body: str | None = Field(default=None, max_length=20000)
    uri: str | None = Field(default=None, max_length=2000)


class ResourceResponse(BaseModel):
    id: UUID
    project_id: UUID
    kind: ResourceKind
    title: str
    body: str | None
    uri: str | None
    created_at: datetime
    updated_at: datetime


class ComponentAnswerItem(BaseModel):
    framework_id: str = Field(..., min_length=1, max_length=64)
    component_id: str = Field(..., min_length=1, max_length=64)
    question_index: int = Field(..., ge=0, le=100)
    answer: str = Field(..., min_length=1, max_length=20000)


class ComponentAnswerBulkRequest(BaseModel):
    answers: list[ComponentAnswerItem] = Field(..., min_length=1, max_length=200)


class ComponentAnswerResponse(BaseModel):
    id: UUID
    project_id: UUID
    framework_id: str
    component_id: str
    question_index: int
    answer: str
    created_at: datetime
    updated_at: datetime


class ElementScoreUpsertRequest(BaseModel):
    framework_id: str = Field(..., min_length=1, max_length=64)
    element_key: str = Field(..., min_length=1, max_length=128)
    element_kind: ElementKind
    score: dict[str, Any] | list[Any] | None = None
    content: dict[str, Any] | list[Any]
    input_fingerprint: str = Field(..., min_length=8, max_length=128)
    mark_stale_on_fingerprint_change: bool = True


class ElementScoreResponse(BaseModel):
    id: UUID
    project_id: UUID
    framework_id: str
    element_key: str
    element_kind: ElementKind
    score: dict[str, Any] | list[Any] | None
    content: dict[str, Any] | list[Any]
    input_fingerprint: str
    is_stale: bool
    computed_at: datetime


class ComponentResultRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    framework_id: str = Field(..., min_length=1, max_length=64)
    regenerate: bool = False
    model_provider: Literal["openai", "google"] | None = None
    model_id: str | None = Field(default=None, max_length=120)


class ComponentResultResponse(BaseModel):
    project_id: UUID
    framework_id: str
    component_id: str
    text: str
    is_stale: bool
    computed_at: datetime


class ProjectDetailsChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    instruction: str = Field(..., min_length=1, max_length=100000)
    model_provider: Literal["openai", "google"] | None = None
    model_id: str | None = Field(default=None, max_length=120)


class ProjectDetailsImportRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    document: str = Field(..., min_length=1, max_length=500000)
    filename: str | None = Field(default=None, max_length=300)
    model_provider: Literal["openai", "google"] | None = None
    model_id: str | None = Field(default=None, max_length=120)


class ProjectDetailsChatResponse(BaseModel):
    details: str
    summary: str
