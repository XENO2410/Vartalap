# IT Helpdesk — Standard Playbook

## How to Reach IT Helpdesk
| Channel | When to use | SLA |
|---|---|---|
| Self-service portal (Unidesk) | All standard requests / incidents | 4h – 2d depending on priority |
| Phone (extn 40040) | P1 outages only | Immediate |
| Vartalaap `#status` | Track existing ticket status | Real time |

## Password Reset
1. Open https://reset.axisbank.internal.
2. Complete MFA (Authenticator push).
3. Enter your employee ID.
4. Provide the answer to your secret question OR OTP on registered mobile.
5. Set a new password satisfying the policy:
   - Minimum 12 characters.
   - At least 1 uppercase, 1 lowercase, 1 digit, 1 symbol.
   - Cannot reuse the last 5 passwords.

If MFA is not enrolled, raise a ticket via Unidesk with your reporting
manager on CC. SLA: 4 working hours.

## VPN Access Request
1. Raise SR under `IT Helpdesk > Connectivity > VPN`.
2. Attach business justification.
3. Approval path: reporting manager → InfoSec → Network Ops.
4. Provisioning SLA: 2 business days.

## Hardware Issues
- Log a Unidesk ticket under `IT Helpdesk > Hardware`.
- Select the asset type (laptop / desktop / peripheral).
- On-site engineer visit SLA:
  - P1 (screen dead, keyboard dead, no boot): 4 hours.
  - P2 (battery drain, key dropping): next business day.

## Application Access
Requests for internal applications (Unidesk, Finacle, Kaleidoscope) are
raised via `IT Helpdesk > Application Access`. Access requires:
- Role justification from reporting manager.
- Data owner approval.
- InfoSec review (only for regulated apps).

## Reference
- Playbook code: IT-HD-2026-02
- Owner: IT Service Management team.
