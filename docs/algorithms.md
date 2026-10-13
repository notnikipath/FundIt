# Algorithms

## Success forecast (A1)

`success_score = f(progress_pct, days_left, updates_count, comments_count)`

- Progress contributes the largest share
- Short remaining time adds urgency bonus
- Engagement adds confidence
- Score is clamped to `[0, 100]`

## Fraud risk (A2)

`risk = f(goal_amount, avg_pledge, pledge_spike_ratio, account_age_days)`

- High goal and high average pledge increase risk
- Sudden spike ratio boosts risk
- New accounts get additional penalty
- Result is in `[0.0, 1.0]`

## Dynamic goal recommendation (A3)

- If campaign significantly overperforms early, recommended goal is increased
- If campaign underperforms near deadline, recommended goal can be reduced
- API allows controlled manual update in safe bounds

## Recommendation ranking

`score = tag_overlap * 5 + category_match * 4 + progress_weight * 3`

- Tag overlap with user interests is primary signal
- Category alignment is secondary signal
- Progress adds social proof

## Parallel payment planning (C2)

The planner computes workers and batch size from target throughput (`payments/min`) and a worker hint. This provides a baseline for queue partitioning and worker autoscaling.
