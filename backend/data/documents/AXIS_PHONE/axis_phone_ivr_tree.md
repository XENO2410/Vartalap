# IVR Tree & Routing

## Inbound Structure
1. Language selection.
2. Service selection: accounts, cards, loans, wealth, complaints.
3. Authentication via account details or OTP.
4. Routing to the topic queue.

## Smart Routing
Repeat callers are routed to the same agent when available. Priority and
Burgundy customers bypass general queues.

## Queue Messaging
Estimated wait is announced and callback-from-queue is offered beyond the
threshold.

Policy code: AP-IVR-2026-01 | Owner: Contact Centre Technology.
