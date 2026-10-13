from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.fundit_common import (
    RewardAssignment,
    RewardAssignRequest,
    RewardDeliveryStatus,
    RewardDeliveryUpdateRequest,
    RewardTier,
    RewardTierCreateRequest,
    Role,
    Settings,
    has_permission,
)

settings = Settings(service_name="reward-service", service_port=8503)
app = FastAPI(title="FundIt Reward Service", version="1.0.0")

reward_tiers: dict[str, RewardTier] = {}
project_tier_ids: dict[str, list[str]] = {}
assignments: dict[str, RewardAssignment] = {}



def _now() -> datetime:
    return datetime.now(UTC)



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")



def _seed_demo() -> None:
    tier_1 = RewardTier(
        tier_id="RWD-STARTER",
        project_id="PRJ-DEMO",
        title="Digital wallpaper pack",
        description="High-resolution art pack and supporter badge.",
        min_amount=900,
        quantity=None,
        delivery_estimate_days=1,
        digital_delivery=True,
    )
    tier_2 = RewardTier(
        tier_id="RWD-KEYBOARD",
        project_id="PRJ-DEMO",
        title="Early bird keyboard",
        description="First-batch keyboard with engraved supporter ID.",
        min_amount=12000,
        quantity=150,
        delivery_estimate_days=90,
        digital_delivery=False,
    )
    reward_tiers[tier_1.tier_id] = tier_1
    reward_tiers[tier_2.tier_id] = tier_2
    project_tier_ids["PRJ-DEMO"] = [tier_1.tier_id, tier_2.tier_id]


_seed_demo()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/tiers")
async def create_tier(request: RewardTierCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "reward:manage")
    tier = RewardTier(
        tier_id=str(uuid4()),
        project_id=request.project_id,
        title=request.title,
        description=request.description,
        min_amount=request.min_amount,
        quantity=request.quantity,
        delivery_estimate_days=request.delivery_estimate_days,
        digital_delivery=request.digital_delivery,
    )
    reward_tiers[tier.tier_id] = tier
    project_tier_ids.setdefault(request.project_id, []).append(tier.tier_id)
    return tier.model_dump(mode="json")


@app.get("/tiers/{tier_id}")
async def get_tier(tier_id: str) -> dict[str, Any]:
    tier = reward_tiers.get(tier_id)
    if tier is None:
        raise HTTPException(status_code=404, detail="Reward tier not found")
    return tier.model_dump(mode="json")


@app.get("/projects/{project_id}/tiers")
async def list_project_tiers(project_id: str) -> dict[str, Any]:
    items = [reward_tiers[tier_id].model_dump(mode="json") for tier_id in project_tier_ids.get(project_id, [])]
    items.sort(key=lambda item: item["min_amount"])
    return {"items": items, "count": len(items)}


@app.post("/rewards/assign")
async def assign_reward(request: RewardAssignRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "reward:claim")
    tier = reward_tiers.get(request.reward_id)
    if tier is None:
        raise HTTPException(status_code=404, detail="Reward tier not found")
    if tier.project_id != request.project_id:
        raise HTTPException(status_code=422, detail="Reward tier belongs to a different project")
    if request.pledge_amount < tier.min_amount:
        raise HTTPException(status_code=422, detail="Pledge amount is lower than tier minimum")
    if tier.quantity is not None and tier.quantity <= 0:
        raise HTTPException(status_code=409, detail="Reward tier is sold out")

    if tier.quantity is not None:
        tier.quantity -= 1

    assignment = RewardAssignment(
        assignment_id=str(uuid4()),
        user_id=request.user_id,
        project_id=request.project_id,
        reward_id=request.reward_id,
        delivery_status=RewardDeliveryStatus.DIGITAL_SENT if tier.digital_delivery else RewardDeliveryStatus.RESERVED,
    )
    assignments[assignment.assignment_id] = assignment

    return {
        "assignment": assignment.model_dump(mode="json"),
        "tier": tier.model_dump(mode="json"),
    }


@app.get("/users/{user_id}/assignments")
async def user_assignments(user_id: str) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in assignments.values() if item.user_id == user_id]
    items.sort(key=lambda item: item["assigned_at"], reverse=True)
    return {"items": items, "count": len(items)}


@app.get("/projects/{project_id}/deliveries")
async def project_deliveries(project_id: str) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in assignments.values() if item.project_id == project_id]
    return {"items": items, "count": len(items)}


@app.post("/assignments/{assignment_id}/delivery")
async def update_delivery(assignment_id: str, request: RewardDeliveryUpdateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "reward:manage")
    assignment = assignments.get(assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.delivery_status = request.status
    assignment.tracking_code = request.tracking_code
    assignment.updated_at = _now()
    return assignment.model_dump(mode="json")


@app.get("/rewards/{tier_id}/ar-preview")
async def ar_preview(tier_id: str) -> dict[str, Any]:
    tier = reward_tiers.get(tier_id)
    if tier is None:
        raise HTTPException(status_code=404, detail="Reward tier not found")
    return {
        "tier_id": tier_id,
        "preview_model_url": f"https://cdn.fundit.local/ar/{tier_id}.glb",
        "instructions": "Open with mobile AR viewer to place reward in your room.",
    }
