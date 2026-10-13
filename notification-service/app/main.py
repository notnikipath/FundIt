from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException

from shared.fundit_common import (
    AuthorPledgeNotificationRequest,
    BackerStatusNotificationRequest,
    NotificationChannel,
    NotificationRequest,
    Role,
    Settings,
    Severity,
    has_permission,
)

settings = Settings(service_name="notification-service", service_port=8507)
app = FastAPI(title="FundIt Notification Service", version="1.0.0")

outbox: list[dict[str, Any]] = []
delivered: list[dict[str, Any]] = []

try:
    from .celery_app import send_email_task
except Exception:  # pragma: no cover - optional during local import
    send_email_task = None



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")



def _mark_delivered(notification_id: str) -> None:
    for item in outbox:
        if item["notification_id"] != notification_id:
            continue
        if item["status"] == "delivered":
            return
        item["status"] = "delivered"
        item["delivered_at"] = datetime.now(UTC).isoformat()
        delivered.append(deepcopy(item))
        return



def _enqueue(
    channel: NotificationChannel,
    recipient: str,
    subject: str,
    body: str,
    severity: Severity,
) -> dict[str, Any]:
    payload = {
        "notification_id": str(uuid4()),
        "channel": channel.value,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "severity": severity.value,
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
        "delivered_at": None,
    }
    outbox.append(payload)
    return payload


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/notify/send")
async def send_notification(request: NotificationRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    _assert_permission(request.actor_role, "notification:send")
    payload = _enqueue(request.channel, request.recipient, request.subject, request.body, request.severity)

    if request.channel == NotificationChannel.EMAIL and send_email_task is not None:
        try:
            send_email_task.delay(request.recipient, request.subject, request.body)
        except Exception:
            background_tasks.add_task(_mark_delivered, payload["notification_id"])
    else:
        background_tasks.add_task(_mark_delivered, payload["notification_id"])

    return payload


@app.post("/notify/author-pledge")
async def notify_author_pledge(
    request: AuthorPledgeNotificationRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    _assert_permission(request.actor_role, "notification:send")
    payload = _enqueue(
        NotificationChannel.IN_APP,
        request.author_id,
        f"New pledge for {request.project_id}",
        f"A new pledge of {request.amount:.2f} {request.currency} was added to your campaign.",
        Severity.INFO,
    )
    background_tasks.add_task(_mark_delivered, payload["notification_id"])
    return payload


@app.post("/notify/backer-status")
async def notify_backer_status(
    request: BackerStatusNotificationRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    _assert_permission(request.actor_role, "notification:send")
    payload = _enqueue(
        NotificationChannel.PUSH,
        request.recipient_id,
        f"Project {request.project_id} status update",
        f"Campaign status changed to: {request.status}",
        Severity.INFO,
    )
    background_tasks.add_task(_mark_delivered, payload["notification_id"])
    return payload


@app.get("/notify/history")
async def history() -> dict[str, Any]:
    return {
        "items": outbox,
        "count": len(outbox),
        "delivered_count": len(delivered),
    }


@app.post("/notify/flush")
async def flush(actor_role: Role = Role.ADMIN) -> dict[str, Any]:
    _assert_permission(actor_role, "notification:send")
    pending = [item for item in outbox if item["status"] != "delivered"]
    for item in pending:
        _mark_delivered(item["notification_id"])
    return {"flushed": len(pending), "total_delivered": len(delivered)}
