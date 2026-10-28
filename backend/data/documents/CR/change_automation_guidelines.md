# Change Automation Guidelines

## Scope
Automation covers CI/CD deployment pipelines, infrastructure-as-code and
self-service standard changes.

## Governance
Automated changes remain governed by the same approval matrix; standard
changes may use pre-approved templates.

## Guardrails
- Automated tests as gates.
- Immutable audit logs.
- Automatic rollback triggers on failure thresholds.

## Exclusions
High-risk and regulatory-impacting changes remain manual unless
specifically approved for automation.

Policy code: CR-AUTO-2026-01 | Owner: DevOps Enablement.
