from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

CATEGORIES = ["creative", "social", "tech", "charity"]
MODELS = ["all_or_nothing", "flexible"]
SOURCES = ["direct", "search", "vk", "email"]


def generate_record(index: int) -> dict:
    goal = random.randint(250_000, 4_500_000)
    pledged = round(goal * random.uniform(0.08, 1.45), 2)
    visits = random.randint(300, 90_000)
    backers = max(1, int(visits * random.uniform(0.01, 0.16)))
    return {
        "project_id": f"PRJ-{index:05d}",
        "author_id": f"AUTH-{random.randint(1, 950):04d}",
        "category": random.choice(CATEGORIES),
        "funding_model": random.choice(MODELS),
        "goal_amount": goal,
        "pledged_amount": pledged,
        "visits": visits,
        "backers": backers,
        "avg_pledge": round(pledged / max(backers, 1), 2),
        "source": random.choice(SOURCES),
        "created_at": (datetime.now(UTC) - timedelta(minutes=index)).isoformat(),
    }


if __name__ == "__main__":
    random.seed(42)
    output = Path(__file__).resolve().parents[1] / "data" / "samples" / "crowdfunding_events.json"
    payload = [generate_record(index) for index in range(1, 12001)]
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} records to {output}")
