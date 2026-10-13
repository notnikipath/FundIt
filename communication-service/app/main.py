from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.fundit_common import (
    Comment,
    CommentCreateRequest,
    DirectMessage,
    DirectMessageRequest,
    ProjectUpdateCreateRequest,
    ProjectUpdatePost,
    Role,
    Settings,
    has_permission,
)

settings = Settings(service_name="communication-service", service_port=8504)
app = FastAPI(title="FundIt Communication Service", version="1.0.0")

updates: list[ProjectUpdatePost] = [
    ProjectUpdatePost(
        update_id="UPD-DEMO-1",
        project_id="PRJ-DEMO",
        author_id="AUTH-100",
        title="Prototype test passed",
        body="The first keyboard prototype passed durability tests. Next milestone: mold optimization.",
    )
]
comments: list[Comment] = [
    Comment(
        comment_id="CMT-DEMO-1",
        project_id="PRJ-DEMO",
        user_id="BACK-07",
        text="Can you share switch compatibility details?",
    )
]
messages: list[DirectMessage] = []



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/updates")
async def create_update(request: ProjectUpdateCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "communication:update")
    if request.is_voice and not request.audio_url:
        raise HTTPException(status_code=422, detail="audio_url is required for voice updates")

    item = ProjectUpdatePost(
        update_id=str(uuid4()),
        project_id=request.project_id,
        author_id=request.author_id,
        title=request.title,
        body=request.body,
        is_voice=request.is_voice,
        audio_url=request.audio_url,
    )
    updates.append(item)
    return item.model_dump(mode="json")


@app.get("/projects/{project_id}/updates")
async def list_updates(project_id: str) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in updates if item.project_id == project_id]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    return {"items": items, "count": len(items)}


@app.post("/comments")
async def create_comment(request: CommentCreateRequest) -> dict[str, Any]:
    if request.actor_role not in {Role.BACKER, Role.AUTHOR, Role.ADMIN}:
        raise HTTPException(status_code=403, detail="Only backers, authors, or admins can comment")

    item = Comment(
        comment_id=str(uuid4()),
        project_id=request.project_id,
        user_id=request.user_id,
        text=request.text,
        parent_id=request.parent_id,
    )
    comments.append(item)
    return item.model_dump(mode="json")


@app.get("/projects/{project_id}/comments")
async def list_comments(project_id: str) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in comments if item.project_id == project_id]
    items.sort(key=lambda item: item["created_at"])
    return {"items": items, "count": len(items)}


@app.post("/messages")
async def send_message(request: DirectMessageRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "communication:message")
    item = DirectMessage(
        message_id=str(uuid4()),
        sender_id=request.sender_id,
        recipient_id=request.recipient_id,
        text=request.text,
    )
    messages.append(item)
    return item.model_dump(mode="json")


@app.get("/messages/thread")
async def message_thread(user_a: str, user_b: str) -> dict[str, Any]:
    items = [
        item.model_dump(mode="json")
        for item in messages
        if {item.sender_id, item.recipient_id} == {user_a, user_b}
    ]
    items.sort(key=lambda item: item["created_at"])
    return {"items": items, "count": len(items)}


@app.get("/messages/inbox/{user_id}")
async def inbox(user_id: str) -> dict[str, Any]:
    items = [item.model_dump(mode="json") for item in messages if item.recipient_id == user_id]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    unread = sum(1 for item in messages if item.recipient_id == user_id and not item.is_read)
    return {"items": items, "count": len(items), "unread": unread}
