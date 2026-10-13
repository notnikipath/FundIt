from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.fundit_common import (
    FundingModel,
    ModerationStatus,
    Project,
    ProjectCategory,
    ProjectCreateRequest,
    ProjectDynamicGoalRequest,
    ProjectModerationRequest,
    ProjectPledgeUpdateRequest,
    ProjectStatus,
    Role,
    Settings,
    build_audit_event,
    dynamic_goal_recommendation,
    has_permission,
)

settings = Settings(service_name="project-service", service_port=8501)
app = FastAPI(title="FundIt Project Service", version="1.0.0")

projects: dict[str, Project] = {}
audit_log: list[dict[str, Any]] = []


class StatusCheckRequest(BaseModel):
    actor_role: Role = Role.AUTHOR


StatusCheckRequest.model_rebuild()



def _now() -> datetime:
    return datetime.now(UTC)


def _seed_demo_project() -> Project:
    now = _now()
    return Project(
        project_id="PRJ-DEMO",
        title="EcoBoard: modular keyboards from recycled plastic",
        short_description="Launch of an eco-friendly keyboard line with open firmware and repairable modules.",
        description=(
            "We build customizable keyboards from recycled ocean plastic. "
            "The campaign funds tooling, first production batch, and open-source firmware support."
        ),
        video_url="https://cdn.fundit.local/videos/eco-board-intro.mp4",
        goal_amount=1_800_000,
        pledged_amount=640_000,
        currency="RUB",
        starts_at=now - timedelta(days=4),
        ends_at=now + timedelta(days=19),
        funding_model=FundingModel.ALL_OR_NOTHING,
        category=ProjectCategory.TECH,
        tags=["hardware", "sustainability", "keyboard", "open-source"],
        author_id="AUTH-100",
        moderation_status=ModerationStatus.APPROVED,
        status=ProjectStatus.ACTIVE,
        backers_count=186,
    )


projects["PRJ-DEMO"] = _seed_demo_project()



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")



def _touch(project: Project) -> None:
    project.updated_at = _now()



def _audit(actor_id: str, actor_role: Role, action: str, object_id: str, details: dict[str, Any] | None = None) -> None:
    audit_log.append(
        build_audit_event(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            object_type="project",
            object_id=object_id,
            details=details or {},
        ).model_dump(mode="json")
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/categories")
async def categories() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {"id": ProjectCategory.CREATIVE.value, "title": "Creative"},
            {"id": ProjectCategory.SOCIAL.value, "title": "Social"},
            {"id": ProjectCategory.TECH.value, "title": "Tech startups"},
            {"id": ProjectCategory.CHARITY.value, "title": "Charity"},
        ]
    }


@app.post("/projects")
async def create_project(request: ProjectCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "project:create")
    if request.ends_at <= request.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be greater than starts_at")

    project = Project(
        project_id=str(uuid4()),
        title=request.title,
        short_description=request.short_description,
        description=request.description,
        video_url=request.video_url,
        goal_amount=request.goal_amount,
        currency=request.currency,
        starts_at=request.starts_at,
        ends_at=request.ends_at,
        funding_model=request.funding_model,
        category=request.category,
        tags=request.tags,
        author_id=request.author_id,
        moderation_status=ModerationStatus.PENDING,
        status=ProjectStatus.MODERATION,
    )
    projects[project.project_id] = project
    _audit(request.author_id, request.actor_role, "project.create", project.project_id)
    return project.model_dump(mode="json")


@app.get("/projects")
async def list_projects(
    status: ProjectStatus | None = None,
    category: ProjectCategory | None = None,
    author_id: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    query_lc = (query or "").lower().strip()

    for project in projects.values():
        if status and project.status != status:
            continue
        if category and project.category != category:
            continue
        if author_id and project.author_id != author_id:
            continue
        if query_lc and query_lc not in project.title.lower() and query_lc not in project.short_description.lower():
            continue
        items.append(project.model_dump(mode="json"))

    items.sort(key=lambda item: item["updated_at"], reverse=True)
    return {"items": items, "count": len(items)}


@app.get("/projects/{project_id}")
async def get_project(project_id: str, actor_role: Role = Role.BACKER) -> dict[str, Any]:
    _assert_permission(actor_role, "project:read")
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.model_dump(mode="json")


@app.post("/projects/{project_id}/moderate")
async def moderate_project(project_id: str, request: ProjectModerationRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "moderation:review")
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.moderation_status = ModerationStatus.APPROVED if request.approve else ModerationStatus.REJECTED
    if request.approve:
        now = _now()
        project.status = ProjectStatus.ACTIVE if now >= project.starts_at else ProjectStatus.DRAFT
    else:
        project.status = ProjectStatus.CANCELLED
    _touch(project)

    _audit(
        request.actor_id,
        request.actor_role,
        "project.moderate",
        project_id,
        {"approved": request.approve, "reason": request.reason},
    )
    return project.model_dump(mode="json")


@app.post("/projects/{project_id}/pledged")
async def update_pledged(project_id: str, request: ProjectPledgeUpdateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "payment:create")
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    now = _now()
    if project.status != ProjectStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="Project is not active")
    if now > project.ends_at:
        project.status = ProjectStatus.ENDED
        _touch(project)
        raise HTTPException(status_code=409, detail="Campaign deadline already passed")

    project.pledged_amount = round(project.pledged_amount + request.amount, 2)
    project.backers_count += 1
    _touch(project)

    _audit(
        request.backer_id,
        request.actor_role,
        "project.pledged.update",
        project_id,
        {"amount": request.amount},
    )
    return project.model_dump(mode="json")


@app.post("/projects/{project_id}/dynamic-goal")
async def dynamic_goal(project_id: str, request: ProjectDynamicGoalRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "project:update")
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    progress_pct = round(project.pledged_amount / max(project.goal_amount, 1) * 100, 2)
    days_left = max((project.ends_at - _now()).days, 0)
    recommended = dynamic_goal_recommendation(project.goal_amount, progress_pct, days_left)

    lower_bound = project.goal_amount * 0.6
    upper_bound = project.goal_amount * 1.6
    if request.new_goal_amount < lower_bound or request.new_goal_amount > upper_bound:
        raise HTTPException(
            status_code=422,
            detail=f"new_goal_amount must be in range [{lower_bound:.2f}, {upper_bound:.2f}]",
        )

    old_goal = project.goal_amount
    project.goal_amount = round(request.new_goal_amount, 2)
    _touch(project)
    _audit(
        request.actor_id,
        request.actor_role,
        "project.goal.dynamic_update",
        project_id,
        {
            "old_goal": old_goal,
            "new_goal": project.goal_amount,
            "recommended": recommended,
            "reason": request.reason,
        },
    )
    return {
        "project": project.model_dump(mode="json"),
        "recommended_goal": recommended,
    }


@app.post("/projects/{project_id}/status-check")
async def status_check(project_id: str, request: StatusCheckRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "project:read")
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    now = _now()
    if project.status in {ProjectStatus.CANCELLED, ProjectStatus.SUCCESSFUL, ProjectStatus.FAILED}:
        return project.model_dump(mode="json")

    if now >= project.ends_at:
        project.status = ProjectStatus.ENDED
        if project.funding_model == FundingModel.ALL_OR_NOTHING:
            if project.pledged_amount >= project.goal_amount:
                project.status = ProjectStatus.SUCCESSFUL
            else:
                project.status = ProjectStatus.FAILED
        elif project.funding_model == FundingModel.FLEXIBLE:
            if project.pledged_amount > 0:
                project.status = ProjectStatus.SUCCESSFUL
            else:
                project.status = ProjectStatus.FAILED
        _touch(project)

    return project.model_dump(mode="json")


@app.get("/audit")
async def get_audit(limit: int = 100, actor_role: Role = Role.ADMIN) -> dict[str, Any]:
    _assert_permission(actor_role, "moderation:review")
    return {"items": audit_log[-limit:]}
