# Axis Phone — Callback Workflow

## What is Axis Phone?
Axis Phone is the assisted-service channel where relationship managers and
contact-centre agents can be requested to call the customer back at a chosen
slot.

## Requesting a Callback (customer path)
1. Customer selects `Axis Phone` in the assistant or on the mobile app.
2. Provides preferred slot (30-minute windows between 09:00 and 20:00 IST).
3. Provides callback number (defaults to the number on file).
4. Selects the topic — `Account queries`, `Loan advisory`, `Cards`,
   `Wealth advisory`, `Complaint`, `Other`.
5. Receives an SMS confirmation with the callback reference ID.

## Assignment
The workflow engine picks an agent by:
- Topic → queue mapping.
- Customer segment (Retail / Priority / Burgundy).
- Language preference (English / Hindi / Regional).
- Agent load balancing — least-active-eligible agent wins.

## SLA
- Priority / Burgundy: **within 15 minutes** of the requested slot.
- Retail: **within 60 minutes**.
- Missed callbacks trigger an auto retry once and are flagged for supervisor
  review.

## Post-Call
- Agent must dispose the call with a valid outcome code and add the call
  summary in the CRM.
- CSAT survey SMS goes out within 30 minutes of call disposition.

## Reference
`AP-CB-2026-01` · Owner: Assisted Channels team.
