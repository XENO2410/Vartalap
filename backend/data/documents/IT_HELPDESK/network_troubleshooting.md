# Network Troubleshooting Playbook

## Wi-Fi / LAN Not Working
1. Check the physical cable / dock is seated firmly.
2. `Windows key + I → Network & Internet → Advanced → Network reset`.
3. Try a different port or the guest wifi to isolate infra vs. laptop.
4. If still failing, open Unidesk under `IT Helpdesk > Connectivity > Wired/Wireless`.

## VPN Disconnect Loop
- Confirm you are on the corporate VPN group in Anyconnect (not the guest
  group).
- Toggle **Airplane mode** for 10 seconds to refresh the network stack.
- Clear the VPN posture cache (`%ProgramData%\Cisco\AnyConnect\posture\ISEPosture.cfg`) and re-launch.
- If disconnects persist within 60 seconds of connect, log a P2 SR — likely
  a certificate issue.

## Slow Application Load
Order of triage:
1. Ping the app endpoint from a command prompt; RTT > 200ms indicates
   backbone congestion.
2. Check `Task Manager > Performance` — is disk I/O at 100%? Might be a
   background AV scan.
3. Check DNS — `nslookup finacle.internal` should return a 10.x address.
4. Clear browser cache & retry.

## Escalation Matrix
| Priority | Definition | SLA |
| --- | --- | --- |
| P1 | Full site / branch down | 15 min response |
| P2 | Individual user, business-critical app | 2 hrs |
| P3 | Individual user, non-critical | Next business day |
| P4 | Enhancement / how-to | 3 business days |

## Reference
`IT-NET-2026-01` · Owner: Network Operations.
