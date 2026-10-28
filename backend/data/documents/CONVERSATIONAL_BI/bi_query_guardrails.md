# Query Guardrails for Conversational BI

## Safety Rules
- Only SELECT queries are generated; no writes or DDL.
- Row limits cap result sizes.
- Query timeouts kill runaway requests.
- Cost limits bind warehouse consumption per session.

## Sensitive Data
The semantic layer masks or excludes raw PAN, account numbers and
customer identifiers unless the user's role permits them.

## Audit
Every generated query, result and user interaction is logged with the
user ID and timestamp.

Policy code: BI-GUARD-2026-01 | Owner: Data Platform team.
