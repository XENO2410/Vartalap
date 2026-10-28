# Environment Strategy

## Environments
Dev, QA, staging and production with defined promotion rules.

## Parity
Staging mirrors production configuration for the change class being
tested. Drift is reconciled before deployment.

## Data
Test environments use masked or synthetic data. Production data in
non-production environments requires approval.

## Access
Environment access follows least privilege; production access is
break-glass controlled.

Policy code: CR-ENV-2026-01 | Owner: Release Management Office.
