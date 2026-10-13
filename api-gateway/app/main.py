from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.fundit_common import PledgeWorkflowRequest, PledgeWorkflowResult, Role, Settings, sign_token, verify_token


class GatewaySettings(BaseSettings):
    service_name: str = "api-gateway"
    service_port: int = 8500

    project_service_url: str = "http://project-service:8501"
    payment_service_url: str = "http://payment-service:8502"
    reward_service_url: str = "http://reward-service:8503"
    communication_service_url: str = "http://communication-service:8504"
    search_service_url: str = "http://search-service:8505"
    analytics_service_url: str = "http://analytics-service:8506"
    notification_service_url: str = "http://notification-service:8507"

    jwt_secret: str = Settings().jwt_secret
    token_exp_minutes: int = 240

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = GatewaySettings()
app = FastAPI(title="FundIt API Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5177",
        "http://127.0.0.1:5177",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:31029",
        "http://127.0.0.1:31029",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    user_id: str
    role: Role
    language: str = Field(default="ru", pattern="^(ru|en)$")


class FinalizeRequest(BaseModel):
    actor_id: str = "SYS-FINALIZER"
    actor_role: Role = Role.ADMIN


AuthRequest.model_rebuild()
FinalizeRequest.model_rebuild()
PledgeWorkflowRequest.model_rebuild()



def _service_urls() -> dict[str, str]:
    return {
        "project": settings.project_service_url,
        "payment": settings.payment_service_url,
        "reward": settings.reward_service_url,
        "communication": settings.communication_service_url,
        "search": settings.search_service_url,
        "analytics": settings.analytics_service_url,
        "notification": settings.notification_service_url,
    }


async def _post_json(client: httpx.AsyncClient, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = await client.post(url, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


async def _get_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = await client.get(url, params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/auth/token")
async def issue_token(request: AuthRequest) -> dict[str, str]:
    token = sign_token(
        {"sub": request.user_id, "role": request.role.value, "language": request.language},
        settings.jwt_secret,
        exp_minutes=settings.token_exp_minutes,
    )
    return {"access_token": token, "token_type": "Bearer"}


@app.post("/auth/verify")
async def verify_auth(token: str) -> dict[str, Any]:
    payload = verify_token(token, settings.jwt_secret)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload


@app.get("/services/health")
async def service_health() -> dict[str, Any]:
    statuses: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        for name, base_url in _service_urls().items():
            try:
                statuses[name] = await _get_json(client, f"{base_url}/health")
            except HTTPException as exc:
                statuses[name] = {"status": "error", "detail": exc.detail}
            except httpx.HTTPError as exc:
                statuses[name] = {"status": "error", "detail": str(exc)}
    return statuses


@app.post("/workflow/pledge")
async def pledge_workflow(request: PledgeWorkflowRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        project = await _get_json(
            client,
            f"{settings.project_service_url}/projects/{request.project_id}",
            {"actor_role": request.actor_role.value},
        )
        if project["status"] != "active":
            raise HTTPException(status_code=409, detail="Project is not active")

        payment = await _post_json(
            client,
            f"{settings.payment_service_url}/payments",
            {
                "user_id": request.user_id,
                "project_id": request.project_id,
                "amount": request.amount,
                "currency": project["currency"],
                "method": request.payment_method.value,
                "actor_role": request.actor_role.value,
            },
        )

        reward_assignment = None
        if request.reward_id:
            try:
                reward_assignment = await _post_json(
                    client,
                    f"{settings.reward_service_url}/rewards/assign",
                    {
                        "user_id": request.user_id,
                        "project_id": request.project_id,
                        "reward_id": request.reward_id,
                        "pledge_amount": request.amount,
                        "actor_id": request.user_id,
                        "actor_role": request.actor_role.value,
                    },
                )
            except HTTPException as exc:
                await _post_json(
                    client,
                    f"{settings.payment_service_url}/payments/{payment['payment_id']}/refund",
                    {
                        "reason": "Reward assignment failed",
                        "actor_id": "SYS-GATEWAY",
                        "actor_role": Role.ADMIN.value,
                    },
                )
                raise HTTPException(status_code=409, detail=f"Reward assignment failed: {exc.detail}") from exc

        project = await _post_json(
            client,
            f"{settings.project_service_url}/projects/{request.project_id}/pledged",
            {
                "amount": request.amount,
                "backer_id": request.user_id,
                "actor_role": request.actor_role.value,
            },
        )

        analytics = await _post_json(
            client,
            f"{settings.analytics_service_url}/analytics/ingest/pledge",
            {
                "project_id": request.project_id,
                "author_id": project["author_id"],
                "user_id": request.user_id,
                "amount": request.amount,
                "goal_amount": project["goal_amount"],
            },
        )

        notification = await _post_json(
            client,
            f"{settings.notification_service_url}/notify/author-pledge",
            {
                "author_id": project["author_id"],
                "project_id": request.project_id,
                "amount": request.amount,
                "currency": project["currency"],
                "actor_role": Role.ADMIN.value,
            },
        )

        await _post_json(
            client,
            f"{settings.search_service_url}/index/project",
            {
                "project_id": project["project_id"],
                "title": project["title"],
                "short_description": project["short_description"],
                "category": project["category"],
                "funding_model": project["funding_model"],
                "tags": project["tags"],
                "goal_amount": project["goal_amount"],
                "pledged_amount": project["pledged_amount"],
                "status": project["status"],
                "author_id": project["author_id"],
                "created_at": project["created_at"],
                "updated_at": project["updated_at"],
            },
            # actor_role is query for this endpoint
        )

    result = PledgeWorkflowResult(
        project=project,
        payment=payment,
        reward_assignment=reward_assignment,
        notification=notification,
        analytics=analytics,
    )
    return result.model_dump(mode="json")


@app.post("/workflow/finalize/{project_id}")
async def finalize_project(project_id: str, request: FinalizeRequest) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        project = await _post_json(
            client,
            f"{settings.project_service_url}/projects/{project_id}/status-check",
            {"actor_role": request.actor_role.value},
        )

        refunds: dict[str, Any] = {"refunded_count": 0, "items": []}
        notifications_sent = 0

        if project["status"] == "failed" and project["funding_model"] == "all_or_nothing":
            refunds = await _post_json(
                client,
                f"{settings.payment_service_url}/refunds/project-failure",
                {
                    "project_id": project_id,
                    "reason": "All-or-nothing campaign failed",
                    "actor_id": request.actor_id,
                    "actor_role": request.actor_role.value,
                },
            )

            refund_sum = round(sum(item["amount"] for item in refunds.get("items", [])), 2)
            if refund_sum > 0:
                await _post_json(
                    client,
                    f"{settings.analytics_service_url}/analytics/ingest/refund",
                    {
                        "project_id": project_id,
                        "author_id": project["author_id"],
                        "amount": refund_sum,
                    },
                )

            for payment in refunds.get("items", []):
                await _post_json(
                    client,
                    f"{settings.notification_service_url}/notify/backer-status",
                    {
                        "recipient_id": payment["user_id"],
                        "project_id": project_id,
                        "status": "failed",
                        "actor_role": request.actor_role.value,
                    },
                )
                notifications_sent += 1

        return {
            "project": project,
            "refunds": refunds,
            "notifications_sent": notifications_sent,
        }


@app.get("/dashboard/{project_id}")
async def project_dashboard(project_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        project = await _get_json(client, f"{settings.project_service_url}/projects/{project_id}")
        rewards = await _get_json(client, f"{settings.reward_service_url}/projects/{project_id}/tiers")
        deliveries = await _get_json(client, f"{settings.reward_service_url}/projects/{project_id}/deliveries")
        updates = await _get_json(client, f"{settings.communication_service_url}/projects/{project_id}/updates")
        comments = await _get_json(client, f"{settings.communication_service_url}/projects/{project_id}/comments")
        payments = await _get_json(client, f"{settings.payment_service_url}/projects/{project_id}/payments")
        analytics = await _get_json(client, f"{settings.analytics_service_url}/analytics/project/{project_id}")
        conversion = await _get_json(
            client,
            f"{settings.analytics_service_url}/analytics/project/{project_id}/conversion",
        )
        try:
            author_report = await _get_json(
                client,
                f"{settings.analytics_service_url}/analytics/author/{project['author_id']}/report",
                {"actor_role": Role.ADMIN.value},
            )
        except HTTPException:
            author_report = {
                "author_id": project["author_id"],
                "projects": [],
                "total_pledged": 0,
                "total_refunds": 0,
                "avg_conversion_pct": 0,
                "avg_progress_pct": 0,
            }
        notices = await _get_json(client, f"{settings.notification_service_url}/notify/history")

    return {
        "project": project,
        "rewards": rewards,
        "deliveries": deliveries,
        "updates": updates,
        "comments": comments,
        "payments": payments,
        "analytics": analytics,
        "conversion": conversion,
        "author_report": author_report,
        "notifications": notices,
    }


@app.get("/discover")
async def discover(
    q: str | None = None,
    category: str | None = None,
    user_id: str | None = None,
    interests: str | None = None,
) -> dict[str, Any]:
    interests_list = [item.strip() for item in (interests or "").split(",") if item.strip()]

    async with httpx.AsyncClient(timeout=20.0) as client:
        search = await _get_json(
            client,
            f"{settings.search_service_url}/search/projects",
            {
                "q": q,
                "category": category,
                "sort": "popular",
                "only_active": True,
                "limit": 12,
            },
        )

        recommendations: dict[str, Any] | None = None
        if user_id:
            recommendations = await _post_json(
                client,
                f"{settings.search_service_url}/recommendations",
                {
                    "user_id": user_id,
                    "interests": interests_list,
                    "viewed_project_ids": [],
                },
            )

    return {
        "search": search,
        "recommendations": recommendations,
    }
