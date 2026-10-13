# Deployment

## Prerequisites

- Docker 24+
- Docker Compose v2

## Environment

Use `.env` at repository root.

Key variables:

- `POSTGRES_DSN`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `PROJECT_SERVICE_URL` ... `NOTIFICATION_SERVICE_URL`
- `VITE_API_GATEWAY_URL`

## Start

```bash
docker compose up --build -d
```

## Stop

```bash
docker compose down
```

## Verification

```bash
docker compose config
python -m ruff check .
python -m pytest -q
```

## Scaling notes

- Scale stateless services with `docker compose up --scale <service>=N`
- Keep Redis and Postgres with persistent volumes
- Use `/payments/throughput/plan` and `/shards/distribution` as scaling guides
