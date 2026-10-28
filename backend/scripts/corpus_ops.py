"""IT_HELPDESK + DOWNLOAD + AHA + AXIS_PHONE corpora.

IT content is grounded in standard ITIL-flavoured service practices and common
enterprise tooling; AHA/Axis Phone/Download content is synthetic. Original prose.
"""

DOCS = [
# ================================================================ IT_HELPDESK
{
 "bubble": "IT_HELPDESK",
 "slug": "laptop_issuance_policy",
 "title": "Laptop Issuance Policy",
 "body": """
## Eligibility
Laptops are issued to all full-time employees in roles requiring mobility.
Desk-bound roles receive desktops unless approved otherwise.

## Configurations
Standard configurations are refreshed periodically: a base model for general
users and a high-spec model for developers and data roles.

## Refresh Cycle
Laptops are refreshed every 36 months. Out-of-cycle refresh needs business-head
approval and is reviewed by IT asset management.

## Return and Transfer
On role change or exit, the device returns to IT for re-imaging. Data is wiped
using certified erasure before reissue.

## Damage and Loss
Accidental damage follows the repair process. Loss must be reported within 24
hours with an FIR where required; recovery charges may apply.

Policy code: IT-LAP-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "laptop_upgrade_policy",
 "title": "Laptop Upgrade Policy",
 "body": """
## Upgrade Triggers
- Device older than 36 months.
- Performance issues verified by IT diagnostics.
- Role change requiring higher specifications.

## Request Flow
Raise a Unidesk request under IT Helpdesk > Hardware > Upgrade with business
justification. IT diagnostics confirm the requirement.

## Approval
Standard upgrades approve via the reporting manager. Out-of-cycle upgrades
require business-head approval.

## Swap Process
The old device is returned, data is migrated by IT, and the new device is
issued within 5 business days of approval.

Policy code: IT-LAP-U-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "software_installation_requests",
 "title": "Software Installation Requests",
 "body": """
## Approved Software
Install from the self-service software centre for approved applications. No
ticket is needed for self-service items.

## New Software
New or unlisted software requires a Unidesk request with business
justification, licence confirmation and InfoSec review.

## Installation
IT pushes approved software remotely. Installations needing admin rights are
scheduled with the user to avoid disruption.

## Licence Compliance
Only licensed software is installed. Personal or unlicensed software is a
policy violation.

Policy code: IT-SW-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "approved_software_list",
 "title": "Approved Software List",
 "body": """
## Categories
- Productivity: office suite, PDF tools, collaboration apps.
- Development: IDEs, version control, database tools (dev roles only).
- Design: approved design tools for marketing and UX.
- Utilities: compression, screenshot and note tools.

## Version Control
Only supported versions are installed. End-of-life versions are blocked
from the network.

## Requesting Additions
Business teams propose additions through the software governance board,
which reviews licences, security and overlap.

## Enforcement
Unauthorised software is detected through the endpoint agent and removed.

Policy code: IT-SW-L-2026-01 | Owner: Software Asset Management.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "printer_support_guide",
 "title": "Printer Support Guide",
 "body": """
## Self-Help First
- Check the printer is powered and online.
- Verify the correct queue is selected.
- Clear stuck jobs from the print queue.

## Raising Tickets
For hardware faults, raise Unidesk under IT Helpdesk > Peripherals > Printer
with the asset tag and error details.

## Toner and Consumables
Toner replacement is requested through the same portal. Consumables stock is
managed by facilities with IT coordination.

## Follow-me Printing
Follow-me printing allows jobs to be released at any networked printer using
the access badge.

Policy code: IT-PRT-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "email_policy",
 "title": "Email Usage Policy",
 "body": """
## Business Use
Corporate email is for business purposes. Personal use must be incidental.

## Security Rules
- Never forward business email to personal accounts.
- Treat external senders with caution; report phishing promptly.
- Use encryption for sensitive attachments as per data classification.

## Retention
Mailbox retention follows the records retention schedule. Legal-hold items are
preserved automatically.

## Signature
Standard signatures are applied centrally; marketing banners need approval.

Policy code: IT-EMAIL-2026-01 | Owner: Collaboration Services.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "mailbox_quota_management",
 "title": "Mailbox Quota Management",
 "body": """
## Default Quota
Standard mailboxes receive the published default quota. Higher quotas need
manager approval.

## Archiving
The mail archiving service offloads older mail automatically. Users can also
archive manually via the client.

## Over-Quota Behaviour
At 90 percent usage, users receive warnings. At 100 percent, sending is
blocked until space is freed.

## Shared Mailboxes
Shared mailboxes carry team quotas and must have a named owner who
reviews access quarterly.

Policy code: IT-MBQ-2026-01 | Owner: Collaboration Services.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "shared_mailbox_management",
 "title": "Shared Mailbox Management",
 "body": """
## Requesting
Shared mailboxes are created on Unidesk request with a business purpose,
owner and initial member list.

## Ownership
Every shared mailbox has a named owner responsible for membership reviews
and housekeeping.

## Access Reviews
Owners confirm membership quarterly. Unused mailboxes are archived after
60 days of inactivity.

## Naming
Mailbox names follow the team naming standard for discoverability.

Policy code: IT-SMB-2026-01 | Owner: Collaboration Services.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "teams_sharepoint_guidelines",
 "title": "Teams & SharePoint Guidelines",
 "body": """
## Team Creation
Teams are created per project or department with an owner and a defined
lifespan. Naming follows the agreed convention.

## Permissions
Use groups, not individuals, for access. External guests require sponsor
approval and expiry dates.

## Data Classification
Sites are labelled by data classification. Confidential sites enforce
stricter sharing rules.

## Lifecycle
Inactive sites are archived after 180 days of inactivity. Owners are
notified 30 days in advance.

Policy code: IT-Collab-2026-01 | Owner: Collaboration Services.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "onedrive_guidelines",
 "title": "OneDrive Usage Guidelines",
 "body": """
## Purpose
OneDrive is the personal work storage for individual documents. Team
documents belong in Teams or SharePoint.

## Sync
Sync only approved folders. Do not sync shared site libraries wholesale
without IT guidance.

## Sharing
Share with named internal users by default. External sharing follows data
classification rules.

## Backup
OneDrive is the primary copy for personal work files. Critical documents
should also exist in team sites.

Policy code: IT-OD-2026-01 | Owner: Collaboration Services.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "remote_desktop_vpn",
 "title": "Remote Desktop & VPN Access",
 "body": """
## VPN Access
VPN connects remote users to internal applications. Access follows the VPN
request workflow with manager and InfoSec approval.

## Remote Desktop
Remote desktop into office workstations is available for approved roles via
the corporate remote-access tool.

## Security Rules
- Use the managed device only.
- Do not share sessions or credentials.
- Disconnect when done; sessions time out after inactivity.

## Troubleshooting
For disconnects, toggle network, restart the VPN client and retry. Persistent
issues raise a P2 ticket.

Policy code: IT-VPN-2026-01 | Owner: Network Operations.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "multi_factor_authentication",
 "title": "Multi-Factor Authentication (MFA)",
 "body": """
## Mandatory MFA
MFA is mandatory for email, VPN, HR systems and all privileged access.
Enrolment happens at onboarding via the authenticator app.

## Methods
Authenticator push is primary; hardware tokens serve users without approved
mobile devices.

## Lockout
Repeated MFA failures lock the account temporarily. Users regain access via
the self-service portal or helpdesk verification.

## New Device
Changing phones requires re-enrolment through the identity portal with a
helpdesk-verified identity check.

Policy code: IT-MFA-2026-01 | Owner: Identity & Access Management.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "phishing_reporting",
 "title": "Phishing & Suspicious Email Reporting",
 "body": """
## Identify
Watch for urgent language, unexpected attachments, mismatched sender domains
and links to unfamiliar sites.

## Report
Use the report-phishing button in the mail client or forward to the security
mailbox. Do not reply or open attachments.

## After Reporting
Delete the mail after reporting. If you clicked a link or opened an
attachment, call the security operations centre immediately.

## Simulations
The bank runs periodic phishing simulations. Reporting simulated messages
correctly is tracked for awareness metrics.

Policy code: IT-PHISH-2026-01 | Owner: Security Operations.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "security_incident_reporting",
 "title": "Security Incident Reporting",
 "body": """
## What to Report
Lost devices, credential compromise, data leakage, malware alerts and
unauthorised access attempts.

## How
Call the security operations centre hotline or raise a Priority-Zero
Unidesk incident. Do not broadcast details on chat channels.

## First Actions
Disconnect the device from the network, do not power off (preserve
evidence), and note what you observed.

## Aftermath
The security team investigates and coordinates with the user on
remediation, which may include password resets and device reimaging.

Policy code: IT-SECIR-2026-01 | Owner: Security Operations.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "it_asset_management",
 "title": "IT Asset Management",
 "body": """
## Asset Register
Every IT asset is recorded with a unique asset tag, user, location and
condition. Moves update the register.

## Custody
Assigned users are custodians and are responsible for reasonable care.
Transfers between employees route through IT.

## Audit
Physical and logical asset audits run annually. Unaccounted assets are
investigated.

## Disposal
End-of-life assets are decommissioned, data-wiped and disposed through
certified recyclers with documentation.

Policy code: IT-ASSET-2026-01 | Owner: IT Asset Management.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "asset_disposal_process",
 "title": "Asset Disposal Process",
 "body": """
## Disposal Triggers
End of refresh cycle, irreparable damage, or technology retirement.

## Steps
1. Remove from the asset register.
2. Certified data erasure with certificate of destruction.
3. Environment-safe disposal through the approved recycler.
4. Closure record with disposal certificate.

## Accountability
Dual control applies to disposal approvals and movement. Certificates are
retained for audit.

Policy code: IT-DISP-2026-01 | Owner: IT Asset Management.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "mobile_device_policy",
 "title": "Corporate Mobile Device Policy",
 "body": """
## Issuance
Corporate mobile devices are issued to roles requiring mobility or
on-call availability, per the eligibility list.

## Management
Devices enrol in mobile device management with enforced passcode, remote
lock and wipe capability.

## Usage
Devices are for business use. Personal apps are limited to the approved
store. International roaming needs approval.

## Loss Reporting
Report loss within 24 hours; the device is remotely wiped. Repeated loss
may attract cost recovery.

Policy code: IT-MDM-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "byod_policy",
 "title": "Bring-Your-Own-Device (BYOD) Policy",
 "body": """
## Scope
BYOD is permitted for email and collaboration apps only, through approved
containerised applications.

## Requirements
Device must meet minimum OS version, have a passcode and allow remote
container wipe.

## Containerisation
Bank data lives in a managed container separated from personal data.
Copying bank data outside the container is blocked.

## De-Enrolment
On exit or device loss, the corporate container is wiped remotely without
touching personal data.

Policy code: IT-BYOD-2026-01 | Owner: End-User Computing.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "guest_wifi_access",
 "title": "Guest Wi-Fi Access",
 "body": """
## Purpose
Guest Wi-Fi provides internet-only access to visitors without exposing the
internal network.

## Access Method
Visitors register with the front desk, receive a time-bound access code,
and connect to the guest SSID.

## Limitations
Guest Wi-Fi cannot reach internal applications. Printing and file shares
are unavailable.

## Security
Guest traffic is isolated and monitored. Unauthorised use of guest access
for business data is prohibited.

Policy code: IT-GWIFI-2026-01 | Owner: Network Operations.
"""
},
{
 "bubble": "IT_HELPDESK",
 "slug": "videoconferencing_rooms",
 "title": "Video-Conference Room Support",
 "body": """
## Booking
Rooms are booked through the collaboration platform with automatic calendar
reservations.

## Equipment
Rooms include display, camera, microphone and one-touch join. Standard
rooms support the approved platforms.

## Etiquette
Mute when not speaking, join from the room device (not personal laptop) and
end meetings on time to free the room.

## Faults
Report room faults under IT Helpdesk > Collaboration > Meeting Rooms with
the room ID. Spare hot-desk kits are available at the IT counter.

Policy code: IT-VCR-2026-01 | Owner: Collaboration Services.
"""
},
# ================================================================ DOWNLOAD
{
 "bubble": "DOWNLOAD",
 "slug": "download_portal_guide",
 "title": "Download Portal User Guide",
 "body": """
## Access
The Download portal is available from the intranet home page and the
वार्तालाप Download bubble.

## Searching
Search by form name, form code or process. Results show the latest version,
effective date and owning department.

## Downloading
Click the form name to preview and download the PDF. Forms are watermarked
with the employee ID for traceability.

## Versions
Only the latest version is served. Superseded versions are archived and
available to process owners on request.

Policy code: DL-PORTAL-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "hr_forms_index",
 "title": "HR Forms Index",
 "body": """
## Leave & Attendance
- HR-LEAVE-01: Special leave application.
- HR-ATT-01: Attendance correction request.
- HR-WFH-01: Remote work declaration.

## Reimbursements
- HR-REIMB-01: Salary reimbursement claim.
- HR-TRVL-01: Travel expense statement.
- HR-ADV-01: Travel advance request.

## Statutory
- HR-PF-NOM-1: Provident fund nomination.
- HR-GRAT-NOM-2: Gratuity nomination.
- HR-TAX-01: Investment declaration form.

## Separation
- HR-RES-01: Resignation form.
- HR-NDC-01: No-dues checklist.

Policy code: DL-HR-2026-01 | Owner: Employee Services.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "statutory_forms_index",
 "title": "Statutory Forms Index",
 "body": """
## FEMA & Remittance
- FEMA-DEC-01: FEMA declaration for inward remittances.
- RBI-INR-05: INR reporting for cross-border trade.

## KYC & FATCA
- KYC-INDV-01: Individual KYC application.
- KYC-CORP-01: Corporate KYC application.
- FATCA-CRS-01: FATCA/CRS self-certification.

## Accounts
- SIG-CHG-01: Signature change request.
- NOM-01: Nomination for savings/current/FD.

## Succession
- CLAIM-SET-01: Claim settlement documentation checklist.

Policy code: DL-STAT-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "it_forms_index",
 "title": "IT Forms Index",
 "body": """
## Access & Services
- IT-SR-01: Standard IT service request template.
- NW-VPN-01: VPN access request template.
- IT-SW-01: New software request form.

## Hardware
- IT-ASSET-01: Asset transfer/return form.
- IT-DISP-01: Asset disposal authorisation.

## Incidents
- IT-SECIR-01: Security incident intake form.

## Approvals
- IT-GENERIC-01: Generic manager approval template for IT requests.

Policy code: DL-IT-2026-01 | Owner: IT Service Management.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "customer_forms_index",
 "title": "Customer Journey Forms Index",
 "body": """
## Onboarding
- CIF-01: Customer information file update.
- KYC-INDV-01 / KYC-CORP-01: KYC applications.

## Accounts & Deposits
- NOM-01: Nomination request.
- FD-MOD-01: Fixed deposit mandate modification.
- SIG-CHG-01: Signature change request.

## Cards & Payments
- CC-ADR-01: Credit card address change.
- ECS-STOP-01: ECS/NACH stop request.

## Grievances
- GRV-01: Customer grievance form.

Policy code: DL-CUST-2026-01 | Owner: Branch Banking Operations.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "branch_ops_forms",
 "title": "Branch Operations Forms Index",
 "body": """
## Cash & Vault
- CASH-ORD-01: Cash ordering and remittance form.
- VAULT-CERT-01: Vault balancing certificate.

## Clearing
- CLG-RET-01: Cheque return register.
- CTS-EXCP-01: CTS exception handling form.

## Compliance
- KYC-REV-01: KYC periodic review checklist.
- AML-ESC-01: AML escalation memo template.

## Reporting
- BR-REP-01: Branch regulatory reporting checklist.

Policy code: DL-BOPS-2026-01 | Owner: Branch Banking Operations.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "compliance_forms_index",
 "title": "Compliance Forms Index",
 "body": """
## Declarations
- COI-01: Conflict of interest declaration.
- GIFT-01: Gift and entertainment register entry.
- INV-01: Investment holding disclosure (designated persons).

## Training
- AML-CERT-01: AML training completion certificate.
- POSH-ACK-01: POSH policy acknowledgement.

## Vendor
- VDD-01: Vendor due-diligence checklist.
- TPR-01: Third-party risk assessment form.

Policy code: DL-COMP-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "finance_forms_index",
 "title": "Finance Forms Index",
 "body": """
## Vendor & Payments
- FIN-VEND-01: New vendor setup form.
- FIN-PAY-01: Payment instruction template.

## Expense & Travel
- FIN-EXP-01: Non-HR expense claim form.
- FIN-ADV-01: Business advance request.

## Budget
- FIN-BUD-01: Budget reallocation request.
- FIN-CAPEX-01: Capital expenditure proposal.

## Approvals
- FIN-DOA-01: Delegation of authority confirmation.

Policy code: DL-FIN-2026-01 | Owner: Finance.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "marketing_assets",
 "title": "Marketing & Brand Assets",
 "body": """
## Templates
- Presentation templates with brand colours and fonts.
- Letterhead and memo templates.

## Logos & Imagery
- Approved logo variants and usage guidelines.
- Photography and illustration library.

## Compliance
Marketing materials referencing products must carry approvals from
compliance and product teams before release.

## Requests
Asset requests route through the brand desk with a stated use case.

Policy code: DL-MKT-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "DOWNLOAD",
 "slug": "form_version_policy",
 "title": "Form Version & Lifecycle Policy",
 "body": """
## Versioning
Forms carry a code, version number and effective date. Minor edits bump the
version; structural changes create a new code.

## Ownership
Every form has an owner responsible for content accuracy and periodic review.

## Review Cycle
Forms are reviewed at least annually. Outdated forms are archived after the
superseding version is published.

## Validation
Only the latest version is valid for submission. Older versions are rejected
by operations.

Policy code: DL-VER-2026-01 | Owner: Process Governance.
"""
},
# ================================================================ AHA
{
 "bubble": "AHA",
 "slug": "aha_portal_guide",
 "title": "Aha Portal User Guide",
 "body": """
## Login
Access the Aha portal with corporate credentials. First login prompts for a
redemption profile setup.

## Dashboard
The dashboard shows point balance, expiring points, recent transactions and
featured redemptions.

## Earning
Points accrue from referrals, cross-sell wins, certifications and
recognition as per the earning matrix.

## Redemption
Browse the catalogue, add items to the cart and check out. E-vouchers are
delivered by email; physical items ship to the registered address.

Policy code: AHA-PORTAL-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_points_earning_matrix",
 "title": "Aha Points Earning Matrix",
 "body": """
## Business Wins
- Successful referral hired: 5,000 points.
- Qualifying cross-sell win: 250 points per unit.
- Audit-clean month for branch/ops team: 500 points.

## Recognition
- Regional CSAT topper: 1,500 points.
- Spot award (manager-issued): 250-1,000 points.
- Long-service milestones: tiered as per tenure.

## Development
- Approved certification pass: 2,000 points.
- Knowledge-sharing session delivered: 300 points.

## Campaigns
Quarterly campaigns publish boosted categories with limited-period
multipliers.

Policy code: AHA-EARN-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_redemption_catalogue",
 "title": "Aha Redemption Catalogue",
 "body": """
## Categories
- E-vouchers: retail, food, travel and wellness brands.
- Merchandise: electronics, home and lifestyle.
- Experiences: curated events and activities.
- Giving: donate points to approved causes.

## Value
Redemption values are published in points per item. Values refresh quarterly
with catalogue updates.

## Delivery
E-vouchers deliver instantly. Physical items ship within 7-10 business days
to the registered address.

## Expiry
Points expire 24 months after award. Expiring points are flagged on the
dashboard 60 days in advance.

Policy code: AHA-REDEEM-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_milestone_awards",
 "title": "Aha Milestone & Long-Service Awards",
 "body": """
## Milestones
Awards are granted at 5, 10, 15, 20 and 25 years of service.

## Award Types
Milestone awards include points, a certificate and a memento as per the
tenure tier.

## Recognition Ceremony
Awards are presented at the annual town hall or regional recognition events.

## Eligibility
Service continuity requirements apply; breaks are handled as per the tenure
calculation rules.

Policy code: AHA-MILE-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_spot_awards",
 "title": "Aha Spot Awards",
 "body": """
## Purpose
Spot awards recognise exceptional contribution between appraisal cycles.

## Issuance
Managers may issue spot awards up to the defined point cap per quarter,
with a short citation.

## Approval
Awards above the manager cap require the next-level approver. HR samples
awards for quality and fairness.

## Visibility
Spot awards are visible to the recipient and their manager. Team-wide
announcements are optional.

Policy code: AHA-SPOT-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_team_awards",
 "title": "Aha Team Awards",
 "body": """
## Categories
- Team of the quarter.
- Collaboration award for cross-functional delivery.
- Customer-impact award.

## Nomination
Nominations open quarterly with business-head endorsement. Teams self-nominate
with a delivery narrative.

## Evaluation
A cross-functional panel scores nominations on impact, collaboration and
customer outcomes.

## Reward
Winning teams receive points per member and a team celebration budget.

Policy code: AHA-TEAM-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_dispute_resolution",
 "title": "Aha Dispute & Point Reversal",
 "body": """
## Dispute Types
- Points not credited within the expected window.
- Clawbacks applied for referrals or wins.
- Redemption not delivered.

## Process
Raise a dispute in the portal under My Points > Raise Dispute with the
transaction reference. SLA is 5 business days.

## Point Reversal
Points are reversed where the underlying transaction is reversed: referral
exit within six months or invalidated cross-sell wins.

## Appeals
Unresolved disputes escalate to the Rewards & Recognition team with a
30-day review window.

Policy code: AHA-DIS-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_quarterly_campaigns",
 "title": "Aha Quarterly Campaigns",
 "body": """
## Structure
Each quarter runs a themed campaign with boosted categories, e.g. referral
months, service-excellence sprints or certification drives.

## Participation
Campaigns auto-track eligible actions. No separate enrolment is needed
unless specified in the campaign brief.

## Leaderboards
Optional leaderboards publish regional or team standings with the
participants' consent.

## Payout
Campaign points credit within 30 days of campaign close.

Policy code: AHA-CAMP-2026-01 | Owner: Rewards & Recognition team.
"""
},
{
 "bubble": "AHA",
 "slug": "aha_faq",
 "title": "Aha FAQ",
 "body": """
## Common Questions
Q: How do I check my balance?
A: The dashboard shows the current balance and the next expiring tranche.

Q: Can I transfer points?
A: No, points are non-transferable. Giving to approved causes is supported.

Q: What if I leave the bank?
A: Unredeemed points lapse on the last working day. Redeem before exit.

Q: Are points taxable?
A: Redemptions may attract perquisite taxation as per prevailing rules,
reflected in payroll.

Policy code: AHA-FAQ-2026-01 | Owner: Rewards & Recognition team.
"""
},
# ================================================================ AXIS_PHONE
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_features",
 "title": "Axis Phone Feature Overview",
 "body": """
## What It Is
Axis Phone is the assisted-service channel where customers request callbacks
from relationship managers and contact-centre agents.

## Core Features
- 30-minute callback slots between 09:00 and 20:00 IST.
- Topic-based routing: accounts, loans, cards, wealth, complaints.
- Language preference support including English, Hindi and regional languages.
- SMS confirmation with a callback reference ID.

## Channels
Callbacks can be requested from the mobile app, internet banking and the
वार्तालाप assistant.

Policy code: AP-OV-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_scheduling",
 "title": "Callback Scheduling Guide",
 "body": """
## Slot Booking
Customers pick a 30-minute window between 09:00 and 20:00 IST on the next
five working days.

## Confirmation
An SMS confirms the slot with a reference ID. The agent sees the booking in
the agent console.

## Rescheduling
Customers can reschedule up to 30 minutes before the slot via the app or the
confirmation SMS link.

## Missed Calls
Missed callbacks retry once automatically, then flag for supervisor
follow-up the next business day.

Policy code: AP-SCH-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_ivr_tree",
 "title": "IVR Tree & Routing",
 "body": """
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
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_language_support",
 "title": "Language Support Framework",
 "body": """
## Supported Languages
English, Hindi, Marathi, Gujarati, Tamil, Telugu, Kannada, Bengali and
Malayalam in assisted channels.

## Preference Capture
Language preference is captured at booking and honoured in routing.

## Agent Matching
The routing engine matches language capability of agents to customer
preference. Overflow uses translation support with disclosure.

## Quality
Calls in regional languages are sampled for quality assurance with
language-certified auditors.

Policy code: AP-LANG-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_priority_handling",
 "title": "Priority Customer Handling",
 "body": """
## Tiers
Priority and Burgundy customers receive dedicated queues and shorter
callbacks.

## SLA
- Priority: callback within 15 minutes of the chosen slot.
- Retail: within 60 minutes.

## Dedicated Teams
Senior agents and relationship teams handle priority queues with warm
context handover from digital channels.

## Escalation
Unresolved priority interactions escalate to the relationship team within
24 hours.

Policy code: AP-PRIO-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_agent_console",
 "title": "Agent Console Guide",
 "body": """
## Layout
The console shows the customer card, interaction history, queue state and
next booking in one view.

## Wrap-Up
Agents dispose every call with a disposition code and a CRM summary before
the next interaction.

## Transfers
Warm transfers preserve context to the receiving agent. Cold transfers need
supervisor approval for priority queues.

## Compliance
Calls are recorded; scripts for disclosures and verifications are mandatory
where defined.

Policy code: AP-CON-2026-01 | Owner: Contact Centre Technology.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_disposition_codes",
 "title": "Call Disposition Codes",
 "body": """
## Code Families
- RES: resolved in first contact.
- FUP: follow-up scheduled.
- TRF: transferred.
- CMP: complaint registered.
- CBK: callback booked.
- NR: no response / voicemail.

## Usage Rules
Every interaction requires one disposition code. Follow-ups must reference
the original interaction ID.

## Reporting
Disposition data feeds first-contact-resolution and repeat-contact metrics.

Policy code: AP-DISP-2026-01 | Owner: Contact Centre Technology.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_callback_sla",
 "title": "Callback SLA Framework",
 "body": """
## Slots and SLA
- Priority/Burgundy: within 15 minutes of the slot.
- Retail: within 60 minutes of the slot.

## Measurement
SLA is measured from slot start to agent connect. Misses count against the
SLA dashboard.

## Breach Handling
Breaches trigger automatic retry, supervisor alerts and root-cause review
for repeat patterns.

## Reporting
Weekly SLA dashboards publish by queue, topic and agent team.

Policy code: AP-SLA-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_escalation_matrix",
 "title": "Escalation Matrix",
 "body": """
## Levels
1. Agent: first contact resolution.
2. Team lead: within same day for unresolved cases.
3. Relationship manager: priority customers.
4. Grievance officer: regulatory or media-flagged cases.

## Timeframes
Each level carries a defined SLA. Missed timeframes escalate automatically.

## Documentation
Every escalation records reason, owner and next action in the CRM.

Policy code: AP-ESC-2026-01 | Owner: Assisted Channels team.
"""
},
{
 "bubble": "AXIS_PHONE",
 "slug": "axis_phone_csat_survey",
 "title": "CSAT Survey Programme",
 "body": """
## Trigger
An SMS survey follows every completed call and callback.

## Questions
One CSAT rating question, one agent-empathy question and an optional
comment.

## Targets
Channel CSAT targets are set quarterly. Results feed agent coaching and
process improvement.

## Closed Loop
Detractors receive a follow-up within 48 hours from the service recovery
team.

Policy code: AP-CSAT-2026-01 | Owner: Assisted Channels team.
"""
},
]
