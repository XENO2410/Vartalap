# Change Request (CR) Standard

## Definition
A **Change Request** is any planned addition, modification or removal of a
production or production-adjacent component that could affect service
availability, integrity or compliance.

## CR Categories
| Category | Approval | Freeze windows apply? |
|---|---|---|
| Standard | Pre-approved template, no CAB | Yes |
| Normal | CAB approval | Yes |
| Emergency | Emergency CAB (E-CAB) | Yes, with waiver |

## Mandatory CR Fields
- Business justification.
- Impact assessment (services, users, data).
- Roll-back plan with owner and time budget.
- Test evidence (unit, integration, UAT sign-off).
- Communication plan.
- Downtime window (if any).

## Freeze Windows
No production CRs during:
- Financial year-end close (last week of March, first week of April).
- Half-yearly close (last week of September, first week of October).
- Regulatory reporting window (2 business days before submission deadline).

## Approval Matrix
| Change scope | Approver |
|---|---|
| Non-prod, single team | Team lead |
| Prod, single service | Service owner |
| Prod, cross-service or data | CAB |
| Regulatory / customer-facing | CAB + Compliance sign-off |

## References
- Standard code: CR-STD-2026-01
- Owner: Change Advisory Board (CAB) secretariat.
