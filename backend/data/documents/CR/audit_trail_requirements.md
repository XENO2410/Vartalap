# Audit Trail Requirements for Changes

## What Must Be Logged
Every CR action: creation, edits, approvals, rejections, implementation
steps and closure, with actor, role and timestamp.

## Immutability
Audit logs are append-only. Administrative changes to logs are themselves
logged.

## Retention
Change records and logs are retained per the records retention policy
and made available to audit.

## Non-Compliance
Missing or altered audit trails are treated as a compliance breach.

Policy code: CR-AUDIT-2026-01 | Owner: Change Management Office.
