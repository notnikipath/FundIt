from __future__ import annotations


def conversion_rate(visitors: int, backers: int) -> float:
    if visitors <= 0:
        return 0.0
    return round(min(max(backers / visitors, 0.0), 1.0) * 100, 2)


def funding_progress(pledged_amount: float, goal_amount: float) -> float:
    if goal_amount <= 0:
        return 0.0
    return round(min(max(pledged_amount / goal_amount, 0.0), 5.0) * 100, 2)


def commission_amount(amount: float, rate: float = 0.05) -> float:
    if amount <= 0:
        return 0.0
    normalized_rate = min(max(rate, 0.0), 0.4)
    return round(amount * normalized_rate, 2)


def success_forecast_score(progress_pct: float, days_left: int, updates_count: int, comments_count: int) -> float:
    momentum = min(max(progress_pct, 0.0), 180.0) * 0.48
    urgency_bonus = max(0, 45 - max(days_left, 0)) * 0.42
    engagement = min(updates_count * 2.8 + comments_count * 0.3, 45)
    return round(min(momentum + urgency_bonus + engagement, 100.0), 2)


def payment_parallel_plan(payments_per_minute: int, workers_hint: int = 6) -> dict[str, int]:
    workers = min(64, max(2, workers_hint, payments_per_minute // 140))
    batch_size = max(20, payments_per_minute // workers) if payments_per_minute > 0 else 20
    return {
        "workers": workers,
        "batch_size": batch_size,
        "payments_per_minute": payments_per_minute,
    }
