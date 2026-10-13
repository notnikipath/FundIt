from datetime import UTC, datetime

from shared.fundit_common import (
    FundingModel,
    ProjectCategory,
    ProjectStatus,
    SearchIndexDocument,
    dynamic_goal_recommendation,
    fraud_risk_score,
    payment_worker_chunks,
    recommend_projects_for_interests,
)


def test_dynamic_goal_recommendation() -> None:
    assert dynamic_goal_recommendation(1_000_000, progress_pct=120, days_left=20) > 1_000_000



def test_fraud_risk_score_in_bounds() -> None:
    score = fraud_risk_score(goal_amount=3_000_000, avg_pledge=80_000, pledge_spike_ratio=2.2, account_age_days=15)
    assert 0 <= score <= 1



def test_payment_worker_chunks() -> None:
    plan = payment_worker_chunks(total_payments=1200, workers=12)
    assert plan["chunk_size"] >= 1



def test_recommend_projects_for_interests() -> None:
    now = datetime.now(UTC)
    projects = [
        SearchIndexDocument(
            project_id="P1",
            title="Open synth",
            short_description="DIY synth project",
            category=ProjectCategory.CREATIVE,
            funding_model=FundingModel.FLEXIBLE,
            tags=["music", "synth"],
            goal_amount=600_000,
            pledged_amount=210_000,
            status=ProjectStatus.ACTIVE,
            author_id="A1",
            created_at=now,
            updated_at=now,
        ),
        SearchIndexDocument(
            project_id="P2",
            title="Medical drone",
            short_description="Emergency medicine delivery",
            category=ProjectCategory.TECH,
            funding_model=FundingModel.ALL_OR_NOTHING,
            tags=["drone", "health"],
            goal_amount=4_000_000,
            pledged_amount=3_600_000,
            status=ProjectStatus.ACTIVE,
            author_id="A2",
            created_at=now,
            updated_at=now,
        ),
    ]
    items = recommend_projects_for_interests(["drone", "tech"], projects)
    assert items
    assert items[0].project_id == "P2"
