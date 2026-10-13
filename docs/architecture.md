# Architecture

## Services

- `api-gateway` - single entrypoint, auth, workflow orchestration
- `project-service` - projects, moderation, statuses, funding goals
- `payment-service` - payment capture, commissions, refunds
- `reward-service` - reward tiers, assignments, delivery updates
- `communication-service` - updates, comments, direct messages
- `analytics-service` - funding metrics, conversion, reports, forecast
- `search-service` - indexing, search, recommendations
- `notification-service` - delivery of status messages and pledge alerts

## Data flow for pledge

1. Gateway reads project state from `project-service`
2. Gateway creates payment in `payment-service`
3. Gateway assigns reward in `reward-service` (optional)
4. Gateway updates pledged amount in `project-service`
5. Gateway pushes analytics event to `analytics-service`
6. Gateway sends author notification through `notification-service`
7. Gateway refreshes search index in `search-service`

## Storage and infrastructure

- PostgreSQL: canonical campaign and financial storage target
- Redis: cache and Celery broker/backend
- Celery worker: async email notifications

## Scalability choices

- Search responses are cached (`TTLCache`)
- Payment throughput endpoint returns worker/batch plan for `1000/min` target
- Category-based shard hints are exposed in search service

## Target quality metrics

- Project page load target: `< 2 sec`
- Payment throughput target: `1000/min`
- Concurrency target: `10,000 users`
