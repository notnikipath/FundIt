# FundIt

FundIt is a microservice crowdfunding platform for creative, social, tech startup, and charity campaigns.

## Implemented modules

- `api-gateway` - auth, orchestration, cross-service workflows
- `project-service` - project creation, moderation, categories, campaign lifecycle
- `payment-service` - pledge collection, fees, refunds, throughput planning
- `reward-service` - reward tiers, assignment, delivery tracking
- `communication-service` - author updates, comments, direct messages
- `analytics-service` - funding statistics, conversion, author reports, forecast
- `search-service` - search, recommendations, cache and shard hints
- `notification-service` - notifications, async email queue, status updates
- `frontend` - campaign dashboard and pledge panel

## Base requirements coverage

1. Project categories: `creative`, `social`, `tech`, `charity`
2. Project module: create, moderate, categorize
3. Payment module: card/YooMoney/e-wallet emulation, refunds, fee calculations
4. Reward module: support tiers and delivery states
5. Communication module: updates, comments, direct messages
6. Analytics module: funding metrics, conversion, author reporting
7. Search/recommendation module: text search and interest-based recommendations

## Optional improvements implemented

- **A1**: project success forecasting (`GET /analytics/forecast/{project_id}`)
- **A2**: fraud risk check (`GET /fraud/check`)
- **A3**: dynamic goal management (`POST /projects/{project_id}/dynamic-goal`)
- **C1**: cached search responses (`TTLCache` in `search-service`)
- **C2**: parallel payment processing plan (`/payments/throughput/plan`)
- **C4**: async email with Celery worker and background fallback
- **D3**: voice update support (`is_voice`, `audio_url`)
- **D4**: AR preview endpoint for rewards

## Tech stack

- Backend: Python FastAPI
- Data: PostgreSQL, Redis
- Queue: Celery
- Payments: Stripe/YooMoney adapters (stub integration)
- Frontend: React + Vite

## Local run

```bash
cd FundIt
docker compose up --build -d
```

## Useful URLs

- Frontend: `http://localhost:5177`
- Gateway health: `http://localhost:8500/health`
- Services health: `http://localhost:8500/services/health`
- Swagger: `http://localhost:8500/docs`

## Validation

```bash
python -m ruff check .
python -m pytest -q
docker compose config
```

## Demo workflow

```bash
python scripts/demo_pipeline.py
```

## Sample data

```bash
python scripts/generate_sample_data.py
```

Result file: `data/samples/crowdfunding_events.json`
