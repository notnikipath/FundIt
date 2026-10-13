from __future__ import annotations

from statistics import mean
from typing import Any

from fastapi import FastAPI, HTTPException

from shared.fundit_common import (
    AnalyticsPledgeEvent,
    AnalyticsRefundEvent,
    AnalyticsVisitEvent,
    Role,
    Settings,
    conversion_rate,
    funding_progress,
    success_forecast_score,
)

settings = Settings(service_name="analytics-service", service_port=8506)
app = FastAPI(title="FundIt Analytics Service", version="1.0.0")

stats: dict[str, dict[str, Any]] = {
    "PRJ-DEMO": {
        "project_id": "PRJ-DEMO",
        "author_id": "AUTH-100",
        "goal_amount": 1_800_000.0,
        "visits": 10_400,
        "pledged_amount": 640_000.0,
        "refund_amount": 0.0,
        "backers": {"BACK-001", "BACK-002", "BACK-003"},
        "updates_count": 2,
        "comments_count": 8,
        "source_breakdown": {"direct": 5200, "vk": 2800, "search": 2400},
    }
}



def _ensure(project_id: str) -> dict[str, Any]:
    payload = stats.setdefault(
        project_id,
        {
            "project_id": project_id,
            "author_id": "UNKNOWN",
            "goal_amount": 1.0,
            "visits": 0,
            "pledged_amount": 0.0,
            "refund_amount": 0.0,
            "backers": set(),
            "updates_count": 0,
            "comments_count": 0,
            "source_breakdown": {},
        },
    )
    return payload



def _project_view(payload: dict[str, Any], days_left: int = 14) -> dict[str, Any]:
    visitors = int(payload["visits"])
    backers_count = len(payload["backers"])
    pledged = float(payload["pledged_amount"])
    refunded = float(payload["refund_amount"])
    goal = float(payload["goal_amount"])
    progress_pct = funding_progress(pledged, goal)
    conversion_pct = conversion_rate(visitors, backers_count)
    forecast = success_forecast_score(progress_pct, days_left, payload["updates_count"], payload["comments_count"])

    return {
        "project_id": payload["project_id"],
        "author_id": payload["author_id"],
        "goal_amount": goal,
        "pledged_amount": pledged,
        "refund_amount": refunded,
        "net_amount": round(max(pledged - refunded, 0.0), 2),
        "visits": visitors,
        "backers_count": backers_count,
        "conversion_pct": conversion_pct,
        "progress_pct": progress_pct,
        "forecast_success_score": forecast,
        "source_breakdown": payload["source_breakdown"],
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/analytics/ingest/visit")
async def ingest_visit(event: AnalyticsVisitEvent) -> dict[str, Any]:
    payload = _ensure(event.project_id)
    payload["visits"] += 1
    payload["source_breakdown"][event.source] = payload["source_breakdown"].get(event.source, 0) + 1
    return {"status": "accepted", "project_id": event.project_id, "visits": payload["visits"]}


@app.post("/analytics/ingest/pledge")
async def ingest_pledge(event: AnalyticsPledgeEvent) -> dict[str, Any]:
    payload = _ensure(event.project_id)
    payload["author_id"] = event.author_id
    payload["goal_amount"] = event.goal_amount
    payload["pledged_amount"] = round(payload["pledged_amount"] + event.amount, 2)
    payload["backers"].add(event.user_id)
    return {
        "status": "accepted",
        "project_id": event.project_id,
        "progress_pct": funding_progress(payload["pledged_amount"], payload["goal_amount"]),
    }


@app.post("/analytics/ingest/refund")
async def ingest_refund(event: AnalyticsRefundEvent) -> dict[str, Any]:
    payload = _ensure(event.project_id)
    payload["author_id"] = event.author_id
    payload["refund_amount"] = round(payload["refund_amount"] + event.amount, 2)
    return {"status": "accepted", "project_id": event.project_id, "refund_amount": payload["refund_amount"]}


@app.post("/analytics/project/{project_id}/engagement")
async def register_engagement(project_id: str, updates_delta: int = 0, comments_delta: int = 0) -> dict[str, Any]:
    payload = _ensure(project_id)
    payload["updates_count"] = max(0, payload["updates_count"] + updates_delta)
    payload["comments_count"] = max(0, payload["comments_count"] + comments_delta)
    return {
        "project_id": project_id,
        "updates_count": payload["updates_count"],
        "comments_count": payload["comments_count"],
    }


@app.get("/analytics/project/{project_id}")
async def project_metrics(project_id: str, days_left: int = 14) -> dict[str, Any]:
    payload = stats.get(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project metrics not found")
    return _project_view(payload, days_left=days_left)


@app.get("/analytics/project/{project_id}/conversion")
async def project_conversion(project_id: str) -> dict[str, Any]:
    payload = stats.get(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project metrics not found")
    visitors = int(payload["visits"])
    backers_count = len(payload["backers"])
    return {
        "project_id": project_id,
        "visits": visitors,
        "backers_count": backers_count,
        "conversion_pct": conversion_rate(visitors, backers_count),
    }


@app.get("/analytics/author/{author_id}/report")
async def author_report(author_id: str, actor_role: Role = Role.AUTHOR) -> dict[str, Any]:
    if actor_role not in {Role.AUTHOR, Role.ADMIN}:
        raise HTTPException(status_code=403, detail="Forbidden")

    items = [_project_view(payload) for payload in stats.values() if payload["author_id"] == author_id]
    if not items:
        raise HTTPException(status_code=404, detail="No projects for this author")

    return {
        "author_id": author_id,
        "projects": items,
        "total_pledged": round(sum(item["pledged_amount"] for item in items), 2),
        "total_refunds": round(sum(item["refund_amount"] for item in items), 2),
        "avg_conversion_pct": round(mean(item["conversion_pct"] for item in items), 2),
        "avg_progress_pct": round(mean(item["progress_pct"] for item in items), 2),
    }


@app.get("/analytics/platform/summary")
async def platform_summary() -> dict[str, Any]:
    items = [_project_view(payload) for payload in stats.values()]
    return {
        "projects": len(items),
        "total_pledged": round(sum(item["pledged_amount"] for item in items), 2),
        "total_refunds": round(sum(item["refund_amount"] for item in items), 2),
        "avg_conversion_pct": round(mean(item["conversion_pct"] for item in items), 2) if items else 0,
        "avg_forecast_score": round(mean(item["forecast_success_score"] for item in items), 2) if items else 0,
        "targets": {
            "project_page_load_seconds": settings.project_page_load_target_seconds,
            "payment_throughput_per_minute": settings.payment_throughput_target_per_minute,
            "concurrent_users": settings.concurrent_users_target,
        },
    }


@app.get("/analytics/forecast/{project_id}")
async def forecast(project_id: str, days_left: int = 14) -> dict[str, Any]:
    payload = stats.get(project_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Project metrics not found")
    metrics = _project_view(payload, days_left=days_left)
    if metrics["forecast_success_score"] >= 70:
        verdict = "high"
    elif metrics["forecast_success_score"] >= 45:
        verdict = "medium"
    else:
        verdict = "low"
    return {
        "project_id": project_id,
        "success_score": metrics["forecast_success_score"],
        "success_probability_level": verdict,
    }
