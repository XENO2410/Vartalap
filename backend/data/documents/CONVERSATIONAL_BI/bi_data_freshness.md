# Data Freshness SLAs

## Tiers
- T0 (real-time/near-real-time): payment and fraud views, up to 15 minutes.
- T1 (daily): business performance and customer metrics, by 09:00 IST.
- T2 (weekly/monthly): HR and survey aggregates.

## Visibility
Each dashboard shows its last refresh timestamp. The assistant quotes
data-as-of dates in answers.

## Breach Handling
Freshness breaches alert the data engineering on-call and are tracked to
resolution.

Policy code: BI-FRESH-2026-01 | Owner: Data Platform team.
