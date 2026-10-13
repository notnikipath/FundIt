from __future__ import annotations

import json
import urllib.request

BASE = "http://localhost:8500"


def request(method: str, path: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    result = request(
        "POST",
        "/workflow/pledge",
        {
            "user_id": "BACK-101",
            "project_id": "PRJ-DEMO",
            "amount": 5000,
            "reward_id": "RWD-STARTER",
            "payment_method": "card",
            "actor_role": "backer",
        },
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
