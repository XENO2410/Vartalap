# Row-Level Security

## Purpose
Row-level security ensures users see only the data their role permits.

## Dimensions
- Geography: zone, region, branch.
- Business: product lines and segments.
- Customer tiers: priority, retail, SME.

## Enforcement
RLS is enforced in the semantic layer, so dashboards and the assistant
inherit identical restrictions.

## Changes
RLS changes route through the data access request workflow with owner
approval.

Policy code: BI-RLS-2026-01 | Owner: Data Governance.
