# Change Management (CR) — Standard Process

## Change Categories
| Category | Definition | Approval |
| --- | --- | --- |
| Standard | Pre-approved template, low risk | Team Lead |
| Normal | Business change with a defined blast radius | CAB |
| Emergency | Production incident fix within 24 hours | Emergency CAB |

## Required Artefacts
Every CR must attach:
1. Business justification and scope.
2. Impact assessment (customer facing? cross-team? regulator? data-migration?).
3. Roll-out plan with owners.
4. Roll-back plan verified in the last drill.
5. Test evidence — unit, integration, UAT.
6. Communication plan (mailer templates, banner text).

## CAB Cadence
- Standing CAB every **Tuesday and Thursday, 16:00 IST**.
- Cut-off for CR submission is 24 hours before CAB.
- Emergency CRs are triaged on demand via the emergency channel.

## Blackout Windows
No non-emergency production changes during:
- Financial year-end (last 5 business days of March).
- Half-year close (last 3 business days of September).
- RBI mandated reporting windows.

## Reference
`CR-STD-2026-01` · Owner: Change Advisory Board.
