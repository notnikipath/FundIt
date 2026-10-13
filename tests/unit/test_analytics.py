
from shared.fundit_common import (
    commission_amount,
    conversion_rate,
    funding_progress,
    payment_parallel_plan,
    success_forecast_score,
)


def test_conversion_rate() -> None:
    assert conversion_rate(1000, 73) == 7.3



def test_funding_progress() -> None:
    assert funding_progress(500_000, 1_000_000) == 50.0



def test_commission_amount() -> None:
    assert commission_amount(10_000, 0.05) == 500.0



def test_success_forecast_score_in_bounds() -> None:
    score = success_forecast_score(progress_pct=62, days_left=11, updates_count=5, comments_count=43)
    assert 0 <= score <= 100



def test_payment_parallel_plan() -> None:
    plan = payment_parallel_plan(payments_per_minute=1000, workers_hint=8)
    assert plan["workers"] >= 2
    assert plan["batch_size"] > 0
