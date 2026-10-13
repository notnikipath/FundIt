# Project Report: FundIt

## Goal

Build a crowdfunding platform for creative, social, startup, and charity projects with two funding models:

- all-or-nothing
- flexible funding

## Delivered architecture

- API gateway + 7 domain microservices
- React frontend dashboard
- PostgreSQL + Redis + Celery worker
- Shared domain package `shared/fundit_common`

## Mandatory requirements mapping

1. **Project module**
   - Create campaigns, moderate, categorize, evaluate final status.
2. **Payments**
   - Collect pledges, compute commissions, refund failed campaigns.
3. **Rewards**
   - Tier management, reward assignment, delivery tracking.
4. **Communication**
   - Author updates, comments, direct messages.
5. **Analytics**
   - Funding stats, conversion, forecast, author reports.
6. **Search and recommendations**
   - Full-text project search and interest-based recommendations.

## Optional improvements delivered

- A1, A2, A3
- C1, C2, C4
- D3, D4

## Quality targets alignment

- Page load target is configured and measurable in analytics settings: `< 2 sec`.
- Payment throughput planning endpoint aligns with `1000/min`.
- Concurrency target `10000` exposed in platform summary.

## Validation

- Unit and integration tests in `tests/`
- Linting with Ruff
- `docker compose config` for deployment integrity

## Conclusion

FundIt provides a complete educational microservice implementation of a crowdfunding platform with strong coverage of required modules and several advanced extensions.
