# Optional Improvements

## Group A

1. **A1 Success Forecasting**
   - Endpoint: `GET /analytics/forecast/{project_id}`
   - Heuristic ML-like score from momentum and engagement.

2. **A2 Fraud Screening**
   - Endpoint: `GET /fraud/check`
   - Risk score based on goal, spikes, average pledge, and account age.

3. **A3 Dynamic Funding Goal**
   - Endpoint: `POST /projects/{project_id}/dynamic-goal`
   - Controlled campaign goal adjustments.

## Group C

1. **C1 Caching**
   - Search query cache with TTL to reduce repeated lookup load.

2. **C2 Parallel Payments Plan**
   - Endpoint: `GET /payments/throughput/plan`
   - Worker and batch recommendations.

3. **C4 Async Email**
   - Celery worker and fallback background task.

## Group D

1. **D3 Voice Updates**
   - Author updates support `is_voice` and `audio_url`.

2. **D4 AR Reward Preview**
   - Endpoint: `GET /rewards/{tier_id}/ar-preview`
   - Returns 3D preview model URL.
