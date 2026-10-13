from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.fundit_common import (
    RecommendationRequest,
    Role,
    SearchIndexDocument,
    SearchSort,
    Settings,
    TTLCache,
    has_permission,
    preferred_categories,
    recommend_projects_for_interests,
)

settings = Settings(service_name="search-service", service_port=8505)
app = FastAPI(title="FundIt Search Service", version="1.0.0")

index: dict[str, SearchIndexDocument] = {
    "PRJ-DEMO": SearchIndexDocument(
        project_id="PRJ-DEMO",
        title="EcoBoard: modular keyboards from recycled plastic",
        short_description="Eco-friendly mechanical keyboard campaign with open firmware.",
        category="tech",
        funding_model="all_or_nothing",
        tags=["hardware", "open-source", "sustainability"],
        goal_amount=1_800_000,
        pledged_amount=640_000,
        status="active",
        author_id="AUTH-100",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
}

cache = TTLCache(ttl_seconds=120)
user_interest_history: dict[str, list[str]] = {}


class BulkIndexRequest(BaseModel):
    items: list[SearchIndexDocument]
    actor_role: Role


BulkIndexRequest.model_rebuild()



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")



def _serialize(items: list[SearchIndexDocument]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]



def _sort(items: list[SearchIndexDocument], sort: SearchSort) -> list[SearchIndexDocument]:
    if sort == SearchSort.POPULAR:
        return sorted(items, key=lambda item: item.pledged_amount, reverse=True)
    if sort == SearchSort.ENDING_SOON:
        return sorted(items, key=lambda item: item.updated_at)
    return sorted(items, key=lambda item: item.created_at, reverse=True)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/index/project")
async def index_project(document: SearchIndexDocument, actor_role: Role = Role.AUTHOR) -> dict[str, Any]:
    _assert_permission(actor_role, "search:index")
    index[document.project_id] = document
    return {"status": "indexed", "project_id": document.project_id}


@app.post("/index/bulk")
async def index_bulk(request: BulkIndexRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "search:index")
    for item in request.items:
        index[item.project_id] = item
    return {"status": "indexed", "count": len(request.items)}


@app.get("/search/projects")
async def search_projects(
    q: str | None = None,
    category: str | None = None,
    funding_model: str | None = None,
    only_active: bool = True,
    sort: SearchSort = SearchSort.NEWEST,
    limit: int = 20,
) -> dict[str, Any]:
    cache_key = f"{q}|{category}|{funding_model}|{only_active}|{sort}|{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return {"items": cached, "count": len(cached), "cached": True}

    q_lc = (q or "").lower().strip()
    items: list[SearchIndexDocument] = []

    for document in index.values():
        if only_active and document.status.value != "active":
            continue
        if category and document.category.value != category:
            continue
        if funding_model and document.funding_model.value != funding_model:
            continue
        if q_lc:
            haystack = f"{document.title} {document.short_description} {' '.join(document.tags)}".lower()
            if q_lc not in haystack:
                continue
        items.append(document)

    sorted_items = _sort(items, sort)[: max(1, min(limit, 100))]
    payload = _serialize(sorted_items)
    cache.set(cache_key, payload)
    return {"items": payload, "count": len(payload), "cached": False}


@app.post("/recommendations")
async def recommendations(request: RecommendationRequest) -> dict[str, Any]:
    history = user_interest_history.setdefault(request.user_id, [])
    history.extend(request.interests)

    interests = request.interests or preferred_categories(history)
    recommended = recommend_projects_for_interests(
        interests,
        list(index.values()),
        excluded_ids=set(request.viewed_project_ids),
        limit=6,
    )
    return {
        "user_id": request.user_id,
        "interests": interests,
        "items": _serialize(recommended),
        "count": len(recommended),
    }


@app.get("/search/suggest")
async def suggest(prefix: str) -> dict[str, Any]:
    prefix_lc = prefix.lower().strip()
    if not prefix_lc:
        return {"items": []}

    candidates: list[str] = []
    for document in index.values():
        if document.title.lower().startswith(prefix_lc):
            candidates.append(document.title)
        for tag in document.tags:
            if tag.lower().startswith(prefix_lc):
                candidates.append(tag)

    deduped = list(dict.fromkeys(candidates))[:8]
    return {"items": deduped}


@app.get("/shards/distribution")
async def shards_distribution() -> dict[str, Any]:
    categories = Counter(doc.category.value for doc in index.values())
    return {
        "categories": dict(categories),
        "shard_hint": "Use category-based sharding for horizontal scaling",
    }


@app.get("/cache/stats")
async def cache_stats() -> dict[str, Any]:
    size = len(cache._store)
    return {"entries": size, "ttl_seconds": cache.ttl}
