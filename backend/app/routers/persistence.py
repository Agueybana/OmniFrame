from __future__ import annotations

from collections.abc import Generator
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import ComponentAnswer, ElementScore, Profile, Project, Resource, utcnow
from ..db.schemas import (
    ComponentAnswerBulkRequest,
    ComponentAnswerResponse,
    ElementScoreResponse,
    ElementScoreUpsertRequest,
    ProfileResponse,
    ProfileUpsertRequest,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
    ResourceCreateRequest,
    ResourceResponse,
    ResourceUpdateRequest,
)
from ..db.session import get_session_factory, is_database_configured

router = APIRouter(prefix="/api", tags=["persistence"])


def require_database() -> None:
    if not is_database_configured():
        raise HTTPException(status_code=503, detail="Database is not configured")


def db_session() -> Generator[Session, None, None]:
    require_database()
    session_factory = get_session_factory()
    if session_factory is None:
        raise HTTPException(status_code=503, detail="Database is not configured")
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def parse_profile_id(profile_id: UUID, header_profile_id: UUID | None = Header(default=None, alias="X-OmniFrame-Profile-Id")) -> UUID:
    if header_profile_id is not None and header_profile_id != profile_id:
        raise HTTPException(status_code=403, detail="Profile header does not match path profile id")
    return profile_id


def get_owned_project(db: Session, project_id: UUID, profile_id: UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        display_name=profile.display_name,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def project_response(project: Project) -> ProjectResponse:
    return ProjectResponse(
        id=project.id,
        profile_id=project.profile_id,
        title=project.title,
        goal=project.goal,
        framework_id=project.framework_id,
        status=project.status,  # type: ignore[arg-type]
        input_fingerprint=project.input_fingerprint,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def resource_response(resource: Resource) -> ResourceResponse:
    return ResourceResponse(
        id=resource.id,
        project_id=resource.project_id,
        kind=resource.kind,  # type: ignore[arg-type]
        title=resource.title,
        body=resource.body,
        uri=resource.uri,
        created_at=resource.created_at,
        updated_at=resource.updated_at,
    )


def answer_response(answer: ComponentAnswer) -> ComponentAnswerResponse:
    return ComponentAnswerResponse(
        id=answer.id,
        project_id=answer.project_id,
        framework_id=answer.framework_id,
        component_id=answer.component_id,
        question_index=answer.question_index,
        answer=answer.answer,
        created_at=answer.created_at,
        updated_at=answer.updated_at,
    )


def score_response(score: ElementScore) -> ElementScoreResponse:
    return ElementScoreResponse(
        id=score.id,
        project_id=score.project_id,
        framework_id=score.framework_id,
        element_key=score.element_key,
        element_kind=score.element_kind,  # type: ignore[arg-type]
        score=score.score,
        content=score.content,
        input_fingerprint=score.input_fingerprint,
        is_stale=score.is_stale,
        computed_at=score.computed_at,
    )


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
def upsert_profile(
    profile_id: UUID,
    payload: ProfileUpsertRequest,
    db: Session = Depends(db_session),
) -> ProfileResponse:
    require_database()
    profile = db.get(Profile, profile_id)
    now = utcnow()
    if profile is None:
        profile = Profile(id=profile_id, display_name=payload.display_name, created_at=now, updated_at=now)
        db.add(profile)
    else:
        profile.display_name = payload.display_name
        profile.updated_at = now
    db.commit()
    db.refresh(profile)
    return profile_response(profile)


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def get_profile(
    profile_id: UUID,
    db: Session = Depends(db_session),
    _: UUID = Depends(parse_profile_id),
) -> ProfileResponse:
    require_database()
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile_response(profile)


@router.get("/profiles/{profile_id}/projects", response_model=list[ProjectResponse])
def list_projects(
    profile_id: UUID,
    db: Session = Depends(db_session),
    _: UUID = Depends(parse_profile_id),
) -> list[ProjectResponse]:
    require_database()
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    projects = db.scalars(
        select(Project).where(Project.profile_id == profile_id).order_by(Project.updated_at.desc())
    ).all()
    return [project_response(project) for project in projects]


@router.post("/profiles/{profile_id}/projects", response_model=ProjectResponse, status_code=201)
def create_project(
    profile_id: UUID,
    payload: ProjectCreateRequest,
    db: Session = Depends(db_session),
    _: UUID = Depends(parse_profile_id),
) -> ProjectResponse:
    require_database()
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    now = utcnow()
    project = Project(
        profile_id=profile_id,
        title=payload.title,
        goal=payload.goal,
        framework_id=payload.framework_id,
        status=payload.status,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_response(project)


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> ProjectResponse:
    require_database()
    project = get_owned_project(db, project_id, profile_id)
    return project_response(project)


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdateRequest,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> ProjectResponse:
    require_database()
    project = get_owned_project(db, project_id, profile_id)
    if payload.title is not None:
        project.title = payload.title
    if payload.goal is not None:
        project.goal = payload.goal
    if payload.framework_id is not None:
        project.framework_id = payload.framework_id
    if payload.status is not None:
        project.status = payload.status
    if payload.input_fingerprint is not None:
        project.input_fingerprint = payload.input_fingerprint
    project.updated_at = utcnow()
    db.commit()
    db.refresh(project)
    return project_response(project)


@router.delete("/projects/{project_id}", status_code=204, response_class=Response)
def delete_project(
    project_id: UUID,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
):
    project = get_owned_project(db, project_id, profile_id)
    db.delete(project)
    db.commit()
    return Response(status_code=204)


@router.get("/projects/{project_id}/resources", response_model=list[ResourceResponse])
def list_resources(
    project_id: UUID,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> list[ResourceResponse]:
    require_database()
    project = get_owned_project(db, project_id, profile_id)
    return [resource_response(resource) for resource in project.resources]


@router.post("/projects/{project_id}/resources", response_model=ResourceResponse, status_code=201)
def create_resource(
    project_id: UUID,
    payload: ResourceCreateRequest,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> ResourceResponse:
    require_database()
    get_owned_project(db, project_id, profile_id)
    now = utcnow()
    resource = Resource(
        project_id=project_id,
        kind=payload.kind,
        title=payload.title,
        body=payload.body,
        uri=payload.uri,
        created_at=now,
        updated_at=now,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource_response(resource)


@router.patch("/resources/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: UUID,
    payload: ResourceUpdateRequest,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> ResourceResponse:
    require_database()
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    get_owned_project(db, resource.project_id, profile_id)
    if payload.kind is not None:
        resource.kind = payload.kind
    if payload.title is not None:
        resource.title = payload.title
    if payload.body is not None:
        resource.body = payload.body
    if payload.uri is not None:
        resource.uri = payload.uri
    resource.updated_at = utcnow()
    db.commit()
    db.refresh(resource)
    return resource_response(resource)


@router.delete("/resources/{resource_id}", status_code=204, response_class=Response)
def delete_resource(
    resource_id: UUID,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
):
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    get_owned_project(db, resource.project_id, profile_id)
    db.delete(resource)
    db.commit()
    return Response(status_code=204)


@router.get("/projects/{project_id}/answers", response_model=list[ComponentAnswerResponse])
def list_answers(
    project_id: UUID,
    framework_id: str | None = Query(default=None),
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> list[ComponentAnswerResponse]:
    require_database()
    get_owned_project(db, project_id, profile_id)
    query = select(ComponentAnswer).where(ComponentAnswer.project_id == project_id)
    if framework_id:
        query = query.where(ComponentAnswer.framework_id == framework_id)
    answers = db.scalars(query.order_by(ComponentAnswer.framework_id, ComponentAnswer.component_id, ComponentAnswer.question_index)).all()
    return [answer_response(answer) for answer in answers]


@router.put("/projects/{project_id}/answers", response_model=list[ComponentAnswerResponse])
def upsert_answers(
    project_id: UUID,
    payload: ComponentAnswerBulkRequest,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> list[ComponentAnswerResponse]:
    require_database()
    get_owned_project(db, project_id, profile_id)
    saved: list[ComponentAnswer] = []
    now = utcnow()
    for item in payload.answers:
        existing = db.scalar(
            select(ComponentAnswer).where(
                ComponentAnswer.project_id == project_id,
                ComponentAnswer.framework_id == item.framework_id,
                ComponentAnswer.component_id == item.component_id,
                ComponentAnswer.question_index == item.question_index,
            )
        )
        if existing is None:
            existing = ComponentAnswer(
                project_id=project_id,
                framework_id=item.framework_id,
                component_id=item.component_id,
                question_index=item.question_index,
                answer=item.answer,
                created_at=now,
                updated_at=now,
            )
            db.add(existing)
        else:
            existing.answer = item.answer
            existing.updated_at = now
        saved.append(existing)
    db.commit()
    for answer in saved:
        db.refresh(answer)
    return [answer_response(answer) for answer in saved]


@router.get("/projects/{project_id}/scores", response_model=list[ElementScoreResponse])
def list_scores(
    project_id: UUID,
    framework_id: str | None = Query(default=None),
    stale_only: bool = Query(default=False),
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> list[ElementScoreResponse]:
    require_database()
    get_owned_project(db, project_id, profile_id)
    query = select(ElementScore).where(ElementScore.project_id == project_id)
    if framework_id:
        query = query.where(ElementScore.framework_id == framework_id)
    if stale_only:
        query = query.where(ElementScore.is_stale.is_(True))
    scores = db.scalars(query.order_by(ElementScore.framework_id, ElementScore.element_key)).all()
    return [score_response(score) for score in scores]


@router.put("/projects/{project_id}/scores", response_model=ElementScoreResponse)
def upsert_score(
    project_id: UUID,
    payload: ElementScoreUpsertRequest,
    db: Session = Depends(db_session),
    profile_id: UUID = Header(..., alias="X-OmniFrame-Profile-Id"),
) -> ElementScoreResponse:
    require_database()
    project = get_owned_project(db, project_id, profile_id)
    now = utcnow()

    if payload.mark_stale_on_fingerprint_change and project.input_fingerprint and project.input_fingerprint != payload.input_fingerprint:
        stale_scores = db.scalars(
            select(ElementScore).where(
                ElementScore.project_id == project_id,
                ElementScore.framework_id == payload.framework_id,
                ElementScore.input_fingerprint != payload.input_fingerprint,
            )
        ).all()
        for score in stale_scores:
            score.is_stale = True

    existing = db.scalar(
        select(ElementScore).where(
            ElementScore.project_id == project_id,
            ElementScore.framework_id == payload.framework_id,
            ElementScore.element_key == payload.element_key,
        )
    )
    if existing is None:
        existing = ElementScore(
            project_id=project_id,
            framework_id=payload.framework_id,
            element_key=payload.element_key,
            element_kind=payload.element_kind,
            score=payload.score,
            content=payload.content,
            input_fingerprint=payload.input_fingerprint,
            is_stale=False,
            computed_at=now,
        )
        db.add(existing)
    else:
        existing.element_kind = payload.element_kind
        existing.score = payload.score
        existing.content = payload.content
        existing.input_fingerprint = payload.input_fingerprint
        existing.is_stale = False
        existing.computed_at = now

    project.updated_at = now
    db.commit()
    db.refresh(existing)
    return score_response(existing)
