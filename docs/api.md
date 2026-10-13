# API Overview

## Gateway

- `GET /health`
- `GET /services/health`
- `POST /auth/token`
- `POST /auth/verify`
- `POST /workflow/pledge`
- `POST /workflow/finalize/{project_id}`
- `GET /dashboard/{project_id}`
- `GET /discover`

## Project service

- `GET /categories`
- `POST /projects`
- `GET /projects`
- `GET /projects/{project_id}`
- `POST /projects/{project_id}/moderate`
- `POST /projects/{project_id}/pledged`
- `POST /projects/{project_id}/dynamic-goal`
- `POST /projects/{project_id}/status-check`

## Payment service

- `POST /payments`
- `GET /payments/{payment_id}`
- `GET /projects/{project_id}/payments`
- `POST /payments/{payment_id}/refund`
- `POST /refunds/project-failure`
- `GET /fees/estimate`
- `GET /payments/throughput/plan`
- `GET /fraud/check`

## Reward service

- `POST /tiers`
- `GET /projects/{project_id}/tiers`
- `POST /rewards/assign`
- `GET /users/{user_id}/assignments`
- `POST /assignments/{assignment_id}/delivery`
- `GET /rewards/{tier_id}/ar-preview`

## Communication service

- `POST /updates`
- `GET /projects/{project_id}/updates`
- `POST /comments`
- `GET /projects/{project_id}/comments`
- `POST /messages`
- `GET /messages/thread`

## Analytics service

- `POST /analytics/ingest/visit`
- `POST /analytics/ingest/pledge`
- `POST /analytics/ingest/refund`
- `GET /analytics/project/{project_id}`
- `GET /analytics/project/{project_id}/conversion`
- `GET /analytics/author/{author_id}/report`
- `GET /analytics/forecast/{project_id}`

## Search service

- `POST /index/project`
- `GET /search/projects`
- `POST /recommendations`
- `GET /search/suggest`
- `GET /shards/distribution`

## Notification service

- `POST /notify/send`
- `POST /notify/author-pledge`
- `POST /notify/backer-status`
- `GET /notify/history`
