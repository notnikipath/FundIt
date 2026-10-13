from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.helpers import load_module

ROOT = Path(__file__).resolve().parents[2]

project_module = load_module("project_module", ROOT / "project-service" / "app" / "main.py")
payment_module = load_module("payment_module", ROOT / "payment-service" / "app" / "main.py")
reward_module = load_module("reward_module", ROOT / "reward-service" / "app" / "main.py")
communication_module = load_module("communication_module", ROOT / "communication-service" / "app" / "main.py")
search_module = load_module("search_module", ROOT / "search-service" / "app" / "main.py")
analytics_module = load_module("analytics_module", ROOT / "analytics-service" / "app" / "main.py")
notification_module = load_module("notification_module", ROOT / "notification-service" / "app" / "main.py")

project_client = TestClient(project_module.app)
payment_client = TestClient(payment_module.app)
reward_client = TestClient(reward_module.app)
communication_client = TestClient(communication_module.app)
search_client = TestClient(search_module.app)
analytics_client = TestClient(analytics_module.app)
notification_client = TestClient(notification_module.app)


def test_pledge_and_reward_flow() -> None:
    project_response = project_client.get("/projects/PRJ-DEMO", params={"actor_role": "backer"})
    assert project_response.status_code == 200

    tiers_response = reward_client.get("/projects/PRJ-DEMO/tiers")
    assert tiers_response.status_code == 200
    tier_id = tiers_response.json()["items"][0]["tier_id"]

    payment_response = payment_client.post(
        "/payments",
        json={
            "user_id": "BACK-900",
            "project_id": "PRJ-DEMO",
            "amount": 5000,
            "currency": "RUB",
            "method": "card",
            "actor_role": "backer",
        },
    )
    assert payment_response.status_code == 200
    payment = payment_response.json()
    assert payment["status"] == "succeeded"

    assign_response = reward_client.post(
        "/rewards/assign",
        json={
            "user_id": "BACK-900",
            "project_id": "PRJ-DEMO",
            "reward_id": tier_id,
            "pledge_amount": 5000,
            "actor_id": "BACK-900",
            "actor_role": "backer",
        },
    )
    assert assign_response.status_code == 200

    project_update = project_client.post(
        "/projects/PRJ-DEMO/pledged",
        json={
            "amount": 5000,
            "backer_id": "BACK-900",
            "actor_role": "backer",
        },
    )
    assert project_update.status_code == 200
    updated_project = project_update.json()

    analytics = analytics_client.post(
        "/analytics/ingest/pledge",
        json={
            "project_id": "PRJ-DEMO",
            "author_id": updated_project["author_id"],
            "user_id": "BACK-900",
            "amount": 5000,
            "goal_amount": updated_project["goal_amount"],
        },
    )
    assert analytics.status_code == 200

    notice = notification_client.post(
        "/notify/author-pledge",
        json={
            "author_id": updated_project["author_id"],
            "project_id": "PRJ-DEMO",
            "amount": 5000,
            "currency": "RUB",
            "actor_role": "admin",
        },
    )
    assert notice.status_code == 200


def test_search_and_communication_flow() -> None:
    update = communication_client.post(
        "/updates",
        json={
            "project_id": "PRJ-DEMO",
            "author_id": "AUTH-100",
            "title": "PCB routing done",
            "body": "The new PCB revision passed the EMI check. We are moving into pilot run planning.",
            "is_voice": False,
            "audio_url": None,
            "actor_role": "author",
        },
    )
    assert update.status_code == 200

    comment = communication_client.post(
        "/comments",
        json={
            "project_id": "PRJ-DEMO",
            "user_id": "BACK-111",
            "text": "Please add ISO layout option.",
            "parent_id": None,
            "actor_role": "backer",
        },
    )
    assert comment.status_code == 200

    message = communication_client.post(
        "/messages",
        json={
            "sender_id": "BACK-111",
            "recipient_id": "AUTH-100",
            "text": "Can I update shipping address later?",
            "actor_role": "backer",
        },
    )
    assert message.status_code == 200

    project = project_client.get("/projects/PRJ-DEMO", params={"actor_role": "backer"}).json()

    indexed = search_client.post(
        "/index/project",
        json={
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
    )
    assert indexed.status_code == 200

    search_response = search_client.get("/search/projects", params={"q": "keyboard"})
    assert search_response.status_code == 200
    assert search_response.json()["count"] >= 1

    recs = search_client.post(
        "/recommendations",
        json={
            "user_id": "BACK-111",
            "interests": ["tech", "hardware"],
            "viewed_project_ids": [],
        },
    )
    assert recs.status_code == 200
    assert recs.json()["count"] >= 1

    metrics = analytics_client.get("/analytics/project/PRJ-DEMO")
    assert metrics.status_code == 200
    assert "conversion_pct" in metrics.json()
