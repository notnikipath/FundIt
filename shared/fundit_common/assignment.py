from __future__ import annotations

from collections import Counter

from .schemas import SearchIndexDocument


def recommend_projects_for_interests(
    interests: list[str],
    projects: list[SearchIndexDocument],
    excluded_ids: set[str] | None = None,
    limit: int = 6,
) -> list[SearchIndexDocument]:
    lowered_interests = {item.lower().strip() for item in interests if item.strip()}
    excluded = excluded_ids or set()
    scored: list[tuple[float, SearchIndexDocument]] = []

    for project in projects:
        if project.project_id in excluded:
            continue
        tag_matches = sum(1 for tag in project.tags if tag.lower() in lowered_interests)
        category_match = 1 if project.category.value in lowered_interests else 0
        progress_weight = min(project.pledged_amount / max(project.goal_amount, 1), 1.2)
        score = tag_matches * 5 + category_match * 4 + progress_weight * 3
        scored.append((score, project))

    scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
    return [item[1] for item in scored[:limit]]


def fraud_risk_score(goal_amount: float, avg_pledge: float, pledge_spike_ratio: float, account_age_days: int) -> float:
    goal_risk = min(goal_amount / 4_000_000, 1.0) * 0.32
    pledge_risk = 0.22 if avg_pledge > 300_000 else 0.08
    spike_risk = min(max(pledge_spike_ratio - 1.0, 0.0), 3.0) / 3.0 * 0.36
    age_risk = 0.2 if account_age_days < 30 else 0.04 if account_age_days < 120 else 0.0
    return round(min(goal_risk + pledge_risk + spike_risk + age_risk, 1.0), 3)


def dynamic_goal_recommendation(current_goal: float, progress_pct: float, days_left: int) -> float:
    if current_goal <= 0:
        return 0.0
    if progress_pct >= 110 and days_left > 7:
        return round(current_goal * 1.2, 2)
    if progress_pct < 35 and days_left <= 5:
        return round(current_goal * 0.8, 2)
    return round(current_goal, 2)


def preferred_categories(history: list[str]) -> list[str]:
    if not history:
        return []
    top = Counter(history).most_common(3)
    return [name for name, _ in top]


def payment_worker_chunks(total_payments: int, workers: int) -> dict[str, int]:
    safe_workers = max(1, workers)
    chunk = max(1, total_payments // safe_workers)
    return {"workers": safe_workers, "chunk_size": chunk, "total_payments": max(total_payments, 0)}
