# Runbook: Internet Banking Deployment

## Pre-Checks

Confirm the change ID, window and rollback plan.

Verify backups and monitoring dashboards are green.

## Execution

1. Announce the deployment in the change channel.

2. Apply the change per the approved steps.

3. Run smoke checks and compare against the baseline.

## Verification

Validate key journeys and batch jobs for the defined observation period.

## Rollback

If smoke checks fail, trigger rollback and notify the service desk immediately.

## Policy code

CR-RUN-INB-2026-01 | Owner: Release Management.