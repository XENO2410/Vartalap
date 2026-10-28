"""Scale the Vartalaap knowledge base to 1000+ FAQs and 500+ documents.

Usage (from the `backend/` directory):
    python -m scripts.scale_kb

Effects
-------
* Deletes previously generated docs (``gen_*.md``) and regenerates them.
* Rewrites ``data/faqs.csv`` = original rows + generated rows (deduped).
* Prints per-bubble document counts and the FAQ total.

Re-run ``python -m scripts.seed_kb --reset`` afterwards to rebuild vectors.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import BACKEND_ROOT  # noqa: E402

DOCS_ROOT = BACKEND_ROOT / "data" / "documents"
FAQS_CSV = BACKEND_ROOT / "data" / "faqs.csv"
DOC_PREFIX = "gen_"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _body(sections: list[tuple[str, list[str]]]) -> str:
    parts: list[str] = []
    for heading, lines in sections:
        parts.append(f"## {heading}")
        parts.extend(lines)
    return "\n\n".join(parts)


def _emit_docs(docs: list[dict]) -> None:
    per_bubble: dict[str, int] = {}
    for doc in docs:
        out_dir = DOCS_ROOT / doc["bubble"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{DOC_PREFIX}{doc['slug']}.md"
        out_path.write_text(f"# {doc['title']}\n\n{doc['body']}", encoding="utf-8")
        per_bubble[doc["bubble"]] = per_bubble.get(doc["bubble"], 0) + 1
    print("Generated docs:")
    for bubble in sorted(per_bubble):
        print(f"  - {bubble}: {per_bubble[bubble]}")
    print(f"  TOTAL: {len(docs)}")


def _clean_generated() -> None:
    removed = 0
    for path in DOCS_ROOT.rglob(f"{DOC_PREFIX}*.md"):
        path.unlink()
        removed += 1
    print(f"Removed {removed} previously generated docs.")


# ---------------------------------------------------------------------------
# FAQ generation
# ---------------------------------------------------------------------------

FAQ_TOPICS: list[dict] = [
    # ============================ HR ============================
    {
        "domain": "HR", "role": "employee", "product": "leave-policy", "freshness": "2026-04-01",
        "slots": [
            {"name": "Privileged Leave", "days": "24 working days", "block": "3 continuous working days", "carry": "carries forward up to a cap of 60 days"},
            {"name": "Casual Leave", "days": "8 working days", "block": "1 working day", "carry": "cannot be carried forward"},
            {"name": "Sick Leave", "days": "12 working days", "block": "1 working day", "carry": "carries forward up to 30 days"},
            {"name": "Maternity Leave", "days": "26 weeks", "block": "continuous", "carry": "does not carry forward"},
            {"name": "Paternity Leave", "days": "15 working days", "block": "continuous", "carry": "does not carry forward"},
            {"name": "Adoption Leave", "days": "12 weeks", "block": "continuous", "carry": "does not carry forward"},
            {"name": "Bereavement Leave", "days": "5 working days", "block": "continuous", "carry": "does not carry forward"},
            {"name": "Sabbatical", "days": "up to 6 months", "block": "continuous", "carry": "does not carry forward"},
            {"name": "Compensatory Off", "days": "1 day per approved weekend day", "block": "a full day", "carry": "carries forward up to 30 days"},
        ],
        "patterns": [
            ("How many days of {name} am I entitled to each year?", "You are entitled to {days} of {name} per calendar year."),
            ("What is the minimum block for {name}?", "The minimum block for {name} is {block}."),
            ("Can {name} be carried forward?", "Unused {name} {carry}."),
            ("How do I apply for {name}?", "Raise the request on the HR self-service portal with the required notice and reporting-manager approval."),
            ("Who approves {name} requests?", "{name} requests are approved by the reporting manager, with HR business partner review for long absences."),
            ("What happens to {name} if I resign?", "On separation, {name} is settled per the full-and-final rules; the balance {carry}."),
        ],
    },
    {
        "domain": "HR", "role": "employee", "product": "attendance", "freshness": "2026-05-01",
        "slots": [
            {"name": "flexible working hours", "rule": "the arrival window is 08:00 to 10:30 IST with a 9-hour workday and core hours of 10:30 to 16:30", "sla": "set with the reporting manager", "who": "reporting manager"},
            {"name": "biometric attendance", "rule": "swipe at entry and exit; missing swipes must be regularised", "sla": "regularise within 3 working days", "who": "HR operations"},
            {"name": "work-from-home", "rule": "up to 2 days per week with a standing declaration", "sla": "register at least 24 hours in advance", "who": "reporting manager"},
            {"name": "late arrival", "rule": "up to 3 late arrivals per month are absorbed; the 4th triggers counselling", "sla": "reviewed monthly", "who": "reporting manager"},
            {"name": "night shift", "rule": "shifts after 20:00 attract shift allowance and transport", "sla": "roster published by the 20th of the prior month", "who": "workforce management"},
            {"name": "attendance correction", "rule": "use HR-ATT-01 to correct any discrepancy", "sla": "processed within 5 working days", "who": "HR operations"},
        ],
        "patterns": [
            ("What are the {name} rules?", "For {name}, {rule}."),
            ("What is the processing time for {name}?", "The turnaround for {name} is: {sla}."),
            ("Who should I contact about {name}?", "Contact the {who} for {name} queries."),
            ("Can I request an exception to {name}?", "Exceptions to {name} require approval from the {who}."),
            ("Where is the {name} policy published?", "The {name} rules live in the attendance policy on the HR intranet."),
        ],
    },
    {
        "domain": "HR", "role": "employee", "product": "reimbursements", "freshness": "2026-05-15",
        "slots": [
            {"name": "mobile bill reimbursement", "limit": "INR 1,500 per month", "cycle": "monthly, by the 5th", "doc": "the phone bill in the employee's name"},
            {"name": "fuel reimbursement", "limit": "approved per-kilometre rates", "cycle": "monthly, with the log sheet", "doc": "the fuel log and receipts"},
            {"name": "relocation reimbursement", "limit": "per the relocation schedule", "cycle": "one-time, within 60 days of the move", "doc": "invoices and the transfer letter"},
            {"name": "late-shift meal reimbursement", "limit": "INR 300 per shift", "cycle": "weekly", "doc": "the shift roster extract"},
            {"name": "professional membership reimbursement", "limit": "one membership per year", "cycle": "annual", "doc": "the membership invoice"},
            {"name": "books and learning reimbursement", "limit": "INR 5,000 per year", "cycle": "quarterly", "doc": "the purchase receipt"},
        ],
        "patterns": [
            ("How much can I claim under {name}?", "The limit for {name} is {limit}."),
            ("How often can I claim {name}?", "Claims for {name} run {cycle}."),
            ("What documents are needed for {name}?", "Attach {doc} to the claim."),
            ("How do I submit a {name} claim?", "Use HR-REIMB-01 on the HR portal with {doc} attached."),
            ("What happens if my {name} claim is rejected?", "Rejections state the reason; correct and resubmit within 10 working days."),
        ],
    },
    {
        "domain": "HR", "role": "employee", "product": "payroll", "freshness": "2026-06-01",
        "slots": [
            {"name": "salary credit", "rule": "salary credits on the 25th of every month, or the next working day if the 25th is a holiday"},
            {"name": "payslip access", "rule": "payslips publish on the HR portal two days before salary credit"},
            {"name": "TDS declaration", "rule": "submit investment declarations by 15 June and proof documents by 15 January"},
            {"name": "PF contribution", "rule": "12 percent of basic pay is contributed by both employer and employee; the UAN is on the payslip"},
            {"name": "leave encashment", "rule": "encashable leave pays with the March salary up to the policy cap"},
            {"name": "salary account change", "rule": "update the new account on the HR portal before the 15th of the month"},
        ],
        "patterns": [
            ("How does {name} work?", "For {name}: {rule}."),
            ("Where can I verify {name}?", "Check the HR portal under Pay & Benefits; supporting details appear on the payslip."),
            ("Who should I contact about {name}?", "Use the payroll helpdesk in the HR portal; the SLA is 2 business days."),
            ("What should I do if {name} looks incorrect?", "Raise a discrepancy ticket with the payslip copy; corrections apply in the next cycle."),
        ],
    },
    {
        "domain": "HR", "role": "employee", "product": "benefits", "freshness": "2026-06-10",
        "slots": [
            {"name": "Group medical cover", "detail": "gives cashless hospitalisation cover for the employee, spouse, two children and parents up to the sum insured"},
            {"name": "Group term life", "detail": "gives life cover equal to a multiple of annual base salary, with mandatory nomination"},
            {"name": "Parental insurance top-up", "detail": "is a voluntary parental cover funded through monthly salary deductions"},
            {"name": "Corporate NPS", "detail": "is the voluntary corporate National Pension System with an employer-contribution option"},
            {"name": "Employee Assistance Programme", "detail": "offers confidential 24x7 counselling for employees and their families"},
            {"name": "Wellness benefit", "detail": "is an annual allowance for fitness or health programmes, claimed with receipts"},
        ],
        "patterns": [
            ("What is {name}?", "{name} {detail}."),
            ("How do I enrol in {name}?", "Enrol during the benefits window each November, or raise a life-event request on the HR portal."),
            ("When does my {name} cover start?", "Cover starts the first day of the month after enrolment, unless a life event applies."),
            ("Who manages {name} queries?", "The benefits helpdesk in the HR portal responds within 2 business days."),
        ],
    },
    {
        "domain": "HR", "role": "employee", "product": "career", "freshness": "2026-07-01",
        "slots": [
            {"name": "internal job posting", "rule": "IJPs publish on the careers portal; apply within 14 days with manager acknowledgement"},
            {"name": "job rotation", "rule": "rotations run 6 months; eligibility requires at least 18 months in the current role"},
            {"name": "promotion review", "rule": "promotions are reviewed in March-April against performance, tenure and panel feedback"},
            {"name": "performance improvement plan", "rule": "a PIP runs 60 days with weekly check-ins and defined milestones"},
            {"name": "secondment", "rule": "secondments of up to 12 months need business-head and HR approval"},
            {"name": "internal certification", "rule": "approved certifications reimburse up to INR 25,000 with a one-year service commitment"},
        ],
        "patterns": [
            ("How does the {name} process work?", "For the {name} process: {rule}."),
            ("Who can apply for {name}?", "Employees meeting the eligibility criteria in the policy; check the posting for specifics."),
            ("What is the approval flow for {name}?", "Apply through the HR portal with manager approval; the HR business partner coordinates."),
            ("Can I appeal a {name} decision?", "Yes, raise an appeal within 10 working days to the next-level manager and HRBP."),
        ],
    },
    # ============================ IT_HELPDESK ============================
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "identity", "freshness": "2026-08-01",
        "slots": [
            {"name": "password reset", "rule": "use the self-service portal with MFA; passwords need 12 characters with upper, digit and symbol", "sla": "immediate via self-service"},
            {"name": "account unlock", "rule": "accounts unlock automatically after 30 minutes; call the helpdesk for urgent access", "sla": "30 minutes"},
            {"name": "MFA enrolment", "rule": "enrol the authenticator app during onboarding; changing devices needs helpdesk verification", "sla": "same business day"},
            {"name": "single sign-on", "rule": "internal applications sign in with corporate credentials; unsupported apps need an SSO onboarding request", "sla": "5 business days"},
            {"name": "leaver access removal", "rule": "access is revoked at end-of-day on the last working day; managers confirm the exit date", "sla": "end of last working day"},
            {"name": "name change", "rule": "update the record through HR first; IT syncs the display name and email within 48 hours", "sla": "48 hours"},
        ],
        "patterns": [
            ("How do I handle a {name}?", "For {name}: {rule}."),
            ("What is the turnaround for {name}?", "The turnaround for {name} is {sla}."),
            ("Who can help with {name}?", "Raise a Unidesk ticket under IT Helpdesk > Identity with your employee ID."),
            ("What if self-service {name} fails?", "Call the IT helpdesk and verify identity with employee ID and manager approval."),
            ("Is manager approval needed for {name}?", "Self-service {name} needs no approval; manual cases require manager sign-off."),
        ],
    },
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "hardware", "freshness": "2026-08-05",
        "slots": [
            {"name": "laptop", "sla": "same-day triage, repair or replacement within 3 business days", "note": "back up your files before handing the device over"},
            {"name": "desktop", "sla": "next-business-day visit for office locations", "note": "monitors and peripherals are covered under facilities"},
            {"name": "monitor", "sla": "replacement within 2 business days from stock", "note": "raise the request with the asset tag"},
            {"name": "docking station", "sla": "replacement within 2 business days", "note": "report the model name in the ticket"},
            {"name": "headset", "sla": "immediate swap at the IT counter for contact-centre staff", "note": "walk-in counter, no ticket needed"},
            {"name": "printer", "sla": "attended within 4 business hours for branches", "note": "quote the printer asset tag"},
        ],
        "patterns": [
            ("How do I report a {name} issue?", "Log a Unidesk ticket under IT Helpdesk > Hardware with the asset tag and a description."),
            ("What is the SLA for {name} issues?", "The SLA for {name} issues is {sla}."),
            ("What should I know before raising a {name} ticket?", "Before raising a {name} ticket: {note}."),
            ("Will I get a loaner {name}?", "Loaners are available for critical roles while the device is under repair."),
            ("How do I track my {name} ticket?", "Track it in Unidesk; escalate to the desk lead if the SLA breaches."),
        ],
    },
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "software", "freshness": "2026-08-10",
        "slots": [
            {"name": "approved software", "rule": "install from the self-service software centre; no ticket is needed"},
            {"name": "new software request", "rule": "raise IT-SW-01 with business justification; InfoSec reviews and the licence is procured"},
            {"name": "licence management", "rule": "licences are tracked centrally; unused licences are reclaimed after 90 days of non-use"},
            {"name": "version upgrades", "rule": "upgrades are pushed remotely with 48 hours notice; unsupported versions are blocked"},
            {"name": "software removal", "rule": "raise a ticket for removal; data is backed up before the uninstall"},
            {"name": "open-source tools", "rule": "open-source tools need a security scan before approval; approval is valid for one year"},
        ],
        "patterns": [
            ("How do I get {name}?", "To get {name}: {rule}."),
            ("What is the approval flow for {name}?", "Reporting manager first, then InfoSec; licences are procured by IT."),
            ("How long does a {name} request take?", "Standard requests complete within 3 business days; procurements can take 10 business days."),
            ("What if my {name} request is rejected?", "The rejection notes the reason; address it and resubmit."),
        ],
    },
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "connectivity", "freshness": "2026-08-15",
        "slots": [
            {"name": "VPN access", "rule": "approved roles get VPN after manager and InfoSec approval; use the managed device only"},
            {"name": "office Wi-Fi", "rule": "connect with corporate credentials on the staff SSID; the guest SSID is for visitors"},
            {"name": "remote desktop", "rule": "remote desktop into office machines is enabled for approved roles via the corporate tool"},
            {"name": "branch connectivity", "rule": "branch links are monitored; outages raise P2 incidents automatically"},
            {"name": "hotspot tethering", "rule": "mobile hotspot use is permitted only when VPN and corporate Wi-Fi are unavailable"},
            {"name": "guest network", "rule": "visitors receive a time-bound code from the front desk; the network has internet only"},
        ],
        "patterns": [
            ("How do I use {name}?", "To use {name}: {rule}."),
            ("What approval is needed for {name}?", "Manager approval plus InfoSec for access to internal systems."),
            ("What do I do when {name} is down?", "Retry after reconnecting; raise a P2 incident with the error code if it persists."),
            ("Is {name} available on personal devices?", "No, {name} is limited to bank-managed devices."),
        ],
    },
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "collaboration", "freshness": "2026-08-20",
        "slots": [
            {"name": "Teams", "rule": "create teams per project or department with a named owner; use groups for permissions"},
            {"name": "SharePoint", "rule": "team sites are for shared documents; labels enforce sharing rules"},
            {"name": "OneDrive", "rule": "personal work storage with known-folder backup; team files belong in Teams"},
            {"name": "shared mailbox", "rule": "request via Unidesk with an owner and members; ownership is reviewed quarterly"},
            {"name": "distribution list", "rule": "request DLs with an owner; membership reviews happen quarterly"},
            {"name": "mailbox quota", "rule": "archive or delete mail above the default quota; sending blocks at 100 percent"},
        ],
        "patterns": [
            ("What is the policy for {name}?", "The {name} policy: {rule}."),
            ("How do I request a new {name}?", "Raise a Unidesk request with the owner, purpose and member list."),
            ("Who manages {name}?", "Each {name} has a named owner; the Collaboration Services team administers."),
            ("What happens to inactive {name}?", "Inactive resources are archived after 180 days with a 30-day owner notice."),
        ],
    },
    {
        "domain": "IT_HELPDESK", "role": "employee", "product": "security", "freshness": "2026-08-25",
        "slots": [
            {"name": "a phishing email", "action": "use the report button in the mail client; do not click links or attachments"},
            {"name": "a lost device", "action": "report within 24 hours; IT wipes the device remotely"},
            {"name": "a malware alert", "action": "disconnect from the network and call the security operations centre"},
            {"name": "a suspicious USB drive", "action": "do not plug it in; hand it to IT security"},
            {"name": "password sharing", "action": "never share credentials; report any request for your password"},
            {"name": "a suspected data leak", "action": "report to the security hotline; do not forward the data further"},
        ],
        "patterns": [
            ("What do I do about {name}?", "For {name}: {action}."),
            ("How quickly must I report {name}?", "Report immediately; some reports carry a 24-hour policy or statutory window."),
            ("Who do I contact for {name}?", "The security operations centre hotline, available 24x7."),
            ("What happens after I report {name}?", "Security investigates, guides remediation and may involve HR or regulators."),
        ],
    },
    # ============================ LAW ============================
    {
        "domain": "LAW", "role": "relationship-manager", "product": "kyc", "freshness": "2026-01-15",
        "slots": [
            {"name": "CDD documentation", "rule": "collect Officially Valid Documents, PAN or Form 60, and a live photograph as per the Master Direction"},
            {"name": "re-KYC timelines", "rule": "high-risk every 2 years, medium every 8 years, low every 10 years"},
            {"name": "PEP checks", "rule": "screen for politically exposed persons and apply enhanced due diligence"},
            {"name": "beneficial ownership", "rule": "identify beneficial owners holding 25 percent or more for non-individual customers"},
            {"name": "video KYC", "rule": "use approved V-CIP for eligible savings accounts with geo-tagging and liveness checks"},
            {"name": "enhanced due diligence", "rule": "apply to PEPs, high-risk jurisdictions and high-value accounts, including source of funds"},
        ],
        "patterns": [
            ("What is {name}?", "For KYC, {name} means: {rule}."),
            ("Which documents are needed for {name}?", "Officially Valid Documents plus PAN or Form 60; non-individuals need constitutional documents."),
            ("How often does {name} apply?", "As per the customer risk category; the Master Direction sets minimum frequencies."),
            ("What happens if {name} is incomplete?", "Account opening or updation is deferred until documents are complete."),
            ("Where do I record {name}?", "Record in the KYC system with the checklist; documents attach to the customer record."),
        ],
    },
    {
        "domain": "LAW", "role": "compliance-officer", "product": "aml", "freshness": "2026-01-20",
        "slots": [
            {"name": "CTR", "rule": "file cash transaction reports within prescribed timelines for cash above the threshold per customer per day"},
            {"name": "STR", "rule": "file suspicious transaction reports within 7 working days of confirming suspicion"},
            {"name": "CCR", "rule": "report counterfeit currency detected at branches promptly to the nodal officer"},
            {"name": "CBWTR", "rule": "report cross-border wire transfers above the threshold with remitter and beneficiary detail"},
            {"name": "AML training", "rule": "all customer-facing staff complete the annual AML e-learning with a passing score"},
            {"name": "record retention", "rule": "maintain KYC and transaction records for the prescribed period after account closure"},
        ],
        "patterns": [
            ("What is {name}?", "{name}: {rule}."),
            ("Who files {name}?", "The Principal Officer files with FIU-IND; branches route details to Financial Crime Compliance."),
            ("What is the timeline for {name}?", "Follow the statutory timeline; late filing is a compliance breach."),
            ("Where can I learn more about {name}?", "The AML intranet page and the annual e-learning module."),
        ],
    },
    {
        "domain": "LAW", "role": "branch-staff", "product": "fraud", "freshness": "2026-02-01",
        "slots": [
            {"name": "cheque fraud", "rule": "verify signatures, crossings and alterations; escalate to the fraud desk for irregular items"},
            {"name": "card fraud", "rule": "block the card on customer confirmation and register the dispute with the card team"},
            {"name": "phishing victims", "rule": "guide customers to report within 3 days to limit liability under RBI rules"},
            {"name": "internal fraud", "rule": "report through the whistleblower channel; preserve records for investigation"},
            {"name": "early warning signals", "rule": "apply branch EWS alerts: sudden balance spikes, frequent large cash, dormant-account revival"},
            {"name": "fraud reporting", "rule": "report frauds above thresholds to the RBI within the prescribed timelines"},
        ],
        "patterns": [
            ("What should I do about {name}?", "For {name}: {rule}."),
            ("Who investigates {name}?", "The fraud risk management unit, with Internal Audit for staff-related cases."),
            ("What is the escalation for {name}?", "Escalate to the zonal fraud desk same-day with the evidence pack."),
            ("Can I inform the customer about {name}?", "Yes, except where an STR is involved — never tip off customers."),
        ],
    },
    {
        "domain": "LAW", "role": "compliance-officer", "product": "dpdp", "freshness": "2026-02-10",
        "slots": [
            {"name": "consent", "rule": "obtain free, specific, informed and unambiguous consent before processing personal data"},
            {"name": "consent withdrawal", "rule": "honour withdrawal as easily as consent was given and stop processing"},
            {"name": "breach notification", "rule": "notify the Data Protection Board within 72 hours of a notifiable breach"},
            {"name": "children's data", "rule": "obtain verifiable parental consent before processing data of minors"},
            {"name": "data principal rights", "rule": "support access, correction, erasure and grievance rights within prescribed timelines"},
            {"name": "consent records", "rule": "retain consent records with timestamps as evidence of lawful processing"},
        ],
        "patterns": [
            ("What does DPDP require for {name}?", "For {name}, DPDP requires: {rule}."),
            ("Who handles {name} at the bank?", "The Data Protection Office; route customer or internal requests to the privacy desk."),
            ("What is the timeline for {name}?", "Respond within the prescribed window and log the action in the privacy register."),
            ("What happens if we miss {name}?", "Regulatory penalty exposure and escalation to the Data Protection Office."),
        ],
    },
    {
        "domain": "LAW", "role": "branch-staff", "product": "consumer", "freshness": "2026-02-15",
        "slots": [
            {"name": "grievance acknowledgement", "rule": "acknowledge every complaint immediately with a reference number"},
            {"name": "complaint resolution", "rule": "resolve standard complaints within 7 working days and complex ones within 30 days"},
            {"name": "ombudsman escalation", "rule": "inform customers of the ombudsman route if the bank rejects or delays beyond 30 days"},
            {"name": "deficiency in service", "rule": "log and rectify service gaps; repeat gaps feed the root-cause review"},
            {"name": "unfair contract terms", "rule": "avoid terms that significantly change consumer rights; use approved documents"},
            {"name": "e-filing", "rule": "guide customers to e-daakhil for consumer commission filings"},
        ],
        "patterns": [
            ("What is the rule on {name}?", "On {name}: {rule}."),
            ("Who owns {name}?", "Customer Advocacy owns the process; branches use the grievance system."),
            ("What are the timelines for {name}?", "As per the Consumer Protection Act and the internal grievance policy."),
            ("Where do I record {name}?", "In the complaint management system with category and resolution notes."),
        ],
    },
    {
        "domain": "LAW", "role": "compliance-officer", "product": "outsourcing", "freshness": "2026-02-20",
        "slots": [
            {"name": "materiality assessment", "rule": "assess outsourcing arrangements for customer impact, data, reporting and continuity"},
            {"name": "vendor audits", "rule": "audit critical vendors at least annually, including data security and sub-contracting"},
            {"name": "exit clauses", "rule": "contracts include data return, destruction certification and transition support"},
            {"name": "sub-contracting", "rule": "restrict sub-contracting without bank consent and re-assessment"},
            {"name": "the outsourcing register", "rule": "maintain a central register for audit and supervisory review"},
            {"name": "board approval", "rule": "material outsourcing requires board or committee approval"},
        ],
        "patterns": [
            ("What is required for {name}?", "For {name}: {rule}."),
            ("Who enforces {name}?", "The Vendor Risk Office with Compliance oversight."),
            ("How often is {name} reviewed?", "Annually at minimum, and on material change."),
        ],
    },
    # ============================ FINANCIAL_ADVISOR ============================
    {
        "domain": "FINANCIAL_ADVISOR", "role": "relationship-manager", "product": "savings-accounts", "freshness": "2026-03-01",
        "slots": [
            {"name": "basic savings", "feature": "zero-balance account per RBI basic savings guidelines", "min": "no minimum balance"},
            {"name": "regular savings", "feature": "tiered interest credited quarterly on daily balances", "min": "minimum balance as per tariff"},
            {"name": "salary account", "feature": "zero-balance with bundled insurance and offers", "min": "no minimum balance"},
            {"name": "premium savings", "feature": "priority service, lounge access and enhanced limits", "min": "a higher relationship balance"},
            {"name": "minor savings", "feature": "operated by the guardian until majority", "min": "no minimum balance for the basic variant"},
            {"name": "NRI savings", "feature": "NRE/NRO variants with repatriation rules per FEMA", "min": "variant-specific"},
        ],
        "patterns": [
            ("What are the features of {name}?", "The {name} account: {feature}; {min}."),
            ("Who is eligible for {name}?", "Eligibility follows the product one-pager; KYC applies to all applicants."),
            ("How is interest calculated on {name}?", "Interest is calculated on daily balances and credited quarterly at prevailing rates."),
            ("What documents are needed for {name}?", "KYC documents plus any variant-specific proof shown in the product guide."),
        ],
    },
    {
        "domain": "FINANCIAL_ADVISOR", "role": "relationship-manager", "product": "credit-cards", "freshness": "2026-03-05",
        "slots": [
            {"name": "card eligibility", "rule": "age 21 to 65, an income threshold by variant and a good bureau score"},
            {"name": "the interest-free period", "rule": "up to the prescribed days from purchase to due date when the full bill is paid"},
            {"name": "EMI conversion", "rule": "convert qualifying purchases into EMIs with the published processing fee"},
            {"name": "credit limit review", "rule": "limits are reviewed periodically based on usage and repayment behaviour"},
            {"name": "card disputes", "rule": "raise disputes within the prescribed days; provisional credit applies per policy"},
            {"name": "rewards redemption", "rule": "redeem points on the rewards portal; points expire per the programme terms"},
        ],
        "patterns": [
            ("What is the rule for {name}?", "For {name}: {rule}."),
            ("Where can a customer check {name}?", "The mobile app, statements and the cardholder agreement."),
            ("How do I explain {name} to a customer?", "Use the approved one-pager and quote exact terms from the agreement."),
            ("What is the SLA for {name} queries?", "Card services respond within 2 business days."),
        ],
    },
    {
        "domain": "FINANCIAL_ADVISOR", "role": "relationship-manager", "product": "loans", "freshness": "2026-03-10",
        "slots": [
            {"name": "personal loan", "note": "unsecured, up to the approved multiple of income, tenure up to the prescribed years"},
            {"name": "home loan", "note": "LTV up to the RBI-permitted ratio, tenure up to the prescribed years, legal and technical evaluation"},
            {"name": "car loan", "note": "funding up to the prescribed percentage of on-road price for new cars"},
            {"name": "education loan", "note": "moratorium of course duration plus the grace period; co-applicant required"},
            {"name": "gold loan", "note": "LTV as per RBI limits, quick disbursal against pledged ornaments"},
        ],
        "patterns": [
            ("What are the key terms of a {name}?", "For a {name}: {note}."),
            ("What documents are needed for a {name}?", "KYC, income proof, and security or purpose documents as per the checklist."),
            ("How is a {name} disbursed?", "Disbursement follows credit approval, agreement execution and security creation."),
            ("What should I flag to a {name} customer?", "Charges, prepayment terms and insurance options from the tariff."),
        ],
    },
    {
        "domain": "FINANCIAL_ADVISOR", "role": "relationship-manager", "product": "investments", "freshness": "2026-03-15",
        "slots": [
            {"name": "PPF", "rule": "15-year tenure extendable in 5-year blocks; interest is government-notified and compounded annually"},
            {"name": "NPS", "rule": "defined-contribution retirement account with tier-I and tier-II; regulated by PFRDA"},
            {"name": "Sukanya Samriddhi", "rule": "for the girl child below age 10; matures at 21 or on marriage after 18"},
            {"name": "SCSS", "rule": "for citizens 60 and above; 5-year tenure extendable once; quarterly interest"},
            {"name": "fixed deposit", "rule": "ladderable tenures with monthly, quarterly or cumulative interest options"},
            {"name": "recurring deposit", "rule": "monthly deposits with the same rate as term deposits at opening"},
        ],
        "patterns": [
            ("What are the basics of {name}?", "The basics of {name}: {rule}."),
            ("Who is eligible for {name}?", "Eligibility follows the scheme or product terms; KYC applies."),
            ("What are the tax rules for {name}?", "Deposits may qualify under Section 80C; interest treatment varies by scheme."),
            ("How do I recommend {name}?", "Match the scheme to the customer's horizon, liquidity and tax position."),
        ],
    },
    {
        "domain": "FINANCIAL_ADVISOR", "role": "relationship-manager", "product": "insurance", "freshness": "2026-03-20",
        "slots": [
            {"name": "term insurance", "rule": "pure protection with level, increasing or return-of-premium variants"},
            {"name": "ULIP", "rule": "market-linked plan with a 5-year lock-in and fund switching"},
            {"name": "health insurance", "rule": "individual and family floater plans; explain waiting periods and exclusions"},
            {"name": "motor insurance", "rule": "comprehensive and third-party; premium depends on IDV and add-ons"},
            {"name": "claims support", "rule": "assist with documentation and insurer follow-up; do not promise claim outcomes"},
            {"name": "riders", "rule": "critical illness and accidental death riders enhance base cover"},
        ],
        "patterns": [
            ("What should I know about {name}?", "About {name}: {rule}."),
            ("How is {name} sold through the bank?", "Through the corporate agency arrangement with approved insurers."),
            ("What disclosures are mandatory for {name}?", "IRDAI-compliant disclosures from the product brochure; no promises beyond terms."),
            ("What is the service SLA for {name}?", "Insurance support responds within 3 business days."),
        ],
    },
    {
        "domain": "FINANCIAL_ADVISOR", "role": "wealth-manager", "product": "wealth", "freshness": "2026-03-25",
        "slots": [
            {"name": "wealth tiers", "rule": "Classic, Priority and Burgundy tiers by relationship value"},
            {"name": "portfolio review", "rule": "at least annually, semi-annually for Priority and Burgundy"},
            {"name": "risk profiling", "rule": "capacity, tolerance and experience map to Conservative, Moderate and Aggressive bands"},
            {"name": "suitability", "rule": "products outside the risk band need written client acknowledgement"},
            {"name": "RM coverage", "rule": "Priority and Burgundy clients get dedicated relationship managers"},
            {"name": "governance", "rule": "advisory conversations are recorded and sampled for mis-selling"},
        ],
        "patterns": [
            ("What is {name}?", "For wealth management, {name}: {rule}."),
            ("How does {name} work in practice?", "Follow the advisory playbook; record recommendations and client decisions."),
            ("Who reviews {name}?", "The quality assurance team samples cases; Compliance owns policy."),
            ("What is the escalation for {name} issues?", "Escalate to the wealth desk lead within one business day."),
        ],
    },
    # ============================ CR ============================
    {
        "domain": "CR", "role": "change-owner", "product": "change-lifecycle", "freshness": "2026-04-01",
        "slots": [
            {"name": "draft", "rule": "complete the template with the business case and impact assessment"},
            {"name": "review", "rule": "peer review plus technical and risk review before submission"},
            {"name": "approval", "rule": "route by risk score through the approval matrix"},
            {"name": "implementation", "rule": "execute within the approved window with rollback readiness"},
            {"name": "post-implementation review", "rule": "complete within 5 to 10 working days per change type"},
            {"name": "closure", "rule": "close only after successful implementation and documentation"},
        ],
        "patterns": [
            ("What happens in the {name} stage?", "In the {name} stage: {rule}."),
            ("Who is responsible in the {name} stage?", "The change owner drives the stage; the Change Management Office governs."),
            ("What blocks the {name} stage?", "Incomplete fields or missing evidence return the change to the previous stage."),
        ],
    },
    {
        "domain": "CR", "role": "change-owner", "product": "standard-changes", "freshness": "2026-04-05",
        "slots": [
            {"name": "certificate renewal", "rule": "pre-approved template with annual recurrence; implement in the standard window"},
            {"name": "server patching", "rule": "follow the monthly patch cycle with the change ID per server group"},
            {"name": "configuration change", "rule": "pre-approved for defined parameters; deviations need CAB review"},
            {"name": "scheduled reboot", "rule": "use the maintenance window and the standard template"},
            {"name": "routine deploys", "rule": "CI/CD pipeline deploys with automated gates for pre-approved paths"},
            {"name": "housekeeping tasks", "rule": "log rotation and cleanup tasks follow the standard-change template"},
        ],
        "patterns": [
            ("How is {name} treated?", "For {name}: {rule}."),
            ("What approvals are needed for {name}?", "Pre-approved by CAB through the standard-change template."),
            ("What evidence is required for {name}?", "Automated logs plus a post-change confirmation note."),
        ],
    },
    {
        "domain": "CR", "role": "incident-commander", "product": "emergency-changes", "freshness": "2026-04-10",
        "slots": [
            {"name": "initiation", "rule": "open the emergency CR linked to the incident ID"},
            {"name": "approval", "rule": "two on-call approvers, one manager or above"},
            {"name": "execution", "rule": "execute immediately with the rollback plan documented"},
            {"name": "retrospective", "rule": "post-implementation review within 5 working days"},
            {"name": "abuse prevention", "rule": "pre-planned work must never use the emergency route"},
            {"name": "communication", "rule": "notify stakeholders and the service desk before execution"},
        ],
        "patterns": [
            ("What is the rule for emergency {name}?", "For emergency {name}: {rule}."),
            ("Who authorises emergency {name}?", "The on-call approvers per the emergency matrix."),
            ("What happens after emergency {name}?", "The retrospective reviews effectiveness and control gaps."),
        ],
    },
    {
        "domain": "CR", "role": "change-owner", "product": "change-freeze", "freshness": "2026-04-15",
        "slots": [
            {"name": "year-end freeze", "rule": "last 5 business days of March, no non-essential changes"},
            {"name": "half-year freeze", "rule": "last 3 business days of September"},
            {"name": "festival freeze", "rule": "major sale periods for customer-facing systems"},
            {"name": "RBI window", "rule": "regulatory reporting windows require CIO-approved exceptions"},
            {"name": "exception route", "rule": "freeze exceptions route as emergency changes with CIO approval"},
            {"name": "freeze communication", "rule": "the freeze calendar publishes annually and revises as needed"},
        ],
        "patterns": [
            ("What is the {name}?", "The {name}: {rule}."),
            ("How do I request an exception during the {name}?", "Use the emergency route with CIO approval."),
            ("Who enforces the {name}?", "The Change Management Office with release management."),
        ],
    },
    {
        "domain": "CR", "role": "change-owner", "product": "change-evidence", "freshness": "2026-04-20",
        "slots": [
            {"name": "test results", "rule": "unit, integration and regression outcomes with environment and date"},
            {"name": "UAT sign-off", "rule": "business stakeholder approval with test case coverage"},
            {"name": "performance tests", "rule": "required for changes affecting critical paths"},
            {"name": "rollback drills", "rule": "a validated rollback plan for high-risk changes"},
            {"name": "approval records", "rule": "recorded in the tool with timestamps and approver identity"},
            {"name": "communication evidence", "rule": "stakeholder and service desk notifications before the window"},
        ],
        "patterns": [
            ("What is required for {name}?", "For {name}: {rule}."),
            ("When must {name} be attached?", "Before CAB review; late evidence returns the change to draft."),
            ("Who validates {name}?", "A reviewer outside the delivery team validates completeness."),
        ],
    },
    {
        "domain": "CR", "role": "cab-member", "product": "change-metrics", "freshness": "2026-04-25",
        "slots": [
            {"name": "success rate", "rule": "percentage of changes implemented without incident"},
            {"name": "emergency ratio", "rule": "emergency changes as a share of all changes"},
            {"name": "PIR completion", "rule": "post-implementation reviews completed on time"},
            {"name": "calendar adherence", "rule": "changes executed inside the approved window"},
            {"name": "incident linkage", "rule": "every production change linked to an incident, problem or feature"},
            {"name": "automation adoption", "rule": "share of standard changes executed through automation"},
        ],
        "patterns": [
            ("How is {name} measured?", "The {name} metric: {rule}."),
            ("Who reviews {name}?", "The CAB monthly, with the Change Management Office dashboard."),
            ("What is the target for {name}?", "Targets are set annually and tracked on the monthly dashboard."),
        ],
    },
    # ============================ GENERAL ============================
    {
        "domain": "GENERAL", "role": "employee", "product": "assistant", "freshness": "2026-08-20",
        "slots": [
            {"name": "bubbles", "rule": "knowledge domains that scope the answer; leave unselected to search all"},
            {"name": "feedback", "rule": "use thumbs up or down; feedback routes to bubble owners"},
            {"name": "citations", "rule": "answers cite sources; open a source to verify details"},
            {"name": "data masking", "rule": "customer PII is masked in answers per data policy"},
            {"name": "session logs", "rule": "conversations are logged with user ID for audit"},
            {"name": "limitations", "rule": "knowledge is limited to indexed documents and their freshness dates"},
        ],
        "patterns": [
            ("What are {name}?", "For the assistant, {name}: {rule}."),
            ("How do I use {name}?", "Follow the getting-started guide on the intranet assistant page."),
            ("Who owns {name}?", "The ADI Program Office coordinates; each bubble has an owner."),
            ("Can {name} be changed?", "Requests route through the ADI Program Office for review."),
            ("Where can I learn more about {name}?", "See the assistant FAQ and the usage guidelines."),
        ],
    },
    {
        "domain": "GENERAL", "role": "employee", "product": "knowledge-management", "freshness": "2026-08-25",
        "slots": [
            {"name": "document ownership", "rule": "every document has an owner and a review date"},
            {"name": "content contribution", "rule": "propose documents through the owning team"},
            {"name": "the review cycle", "rule": "documents are reviewed at least annually"},
            {"name": "versioning", "rule": "minor edits bump the version; structural changes create a new code"},
            {"name": "archival", "rule": "superseded documents archive with a pointer to the successor"},
            {"name": "search", "rule": "use exact terms and department plus topic keywords"},
        ],
        "patterns": [
            ("What is the rule for {name}?", "The rule for {name}: {rule}."),
            ("Who approves {name}?", "The process owner plus compliance review where applicable."),
            ("How do I request {name}?", "Through the KM portal with the owning team copied."),
            ("Where is {name} documented?", "In the document standards and process governance guides."),
        ],
    },
    {
        "domain": "GENERAL", "role": "employee", "product": "learning", "freshness": "2026-08-30",
        "slots": [
            {"name": "mandatory training", "rule": "AML, information security, POSH and code of conduct, with tracked completion"},
            {"name": "enrolment", "rule": "enrol through the learning management system"},
            {"name": "certification", "rule": "approved certifications reimburse per policy with a service commitment"},
            {"name": "learning paths", "rule": "role-based paths from onboarding to leadership"},
            {"name": "training records", "rule": "completions reflect in the employee profile"},
            {"name": "nomination", "rule": "managers nominate for external programmes via the L&D portal"},
        ],
        "patterns": [
            ("What is the policy on {name}?", "The policy on {name}: {rule}."),
            ("How do I complete {name}?", "Log in to the LMS, finish the module and pass the assessment."),
            ("Who tracks {name}?", "Learning & Development with the HR operations team."),
            ("What if I miss {name}?", "Overdue completions flag to the manager and HR."),
        ],
    },
    {
        "domain": "GENERAL", "role": "employee", "product": "corporate", "freshness": "2026-09-01",
        "slots": [
            {"name": "the news feed", "rule": "leadership notes, circulars and events publish on the intranet"},
            {"name": "the corporate directory", "rule": "contact details of teams; do not share externally"},
            {"name": "brand assets", "rule": "templates and logos available from the brand desk"},
            {"name": "the town hall", "rule": "quarterly all-hands with Q&A through the events portal"},
            {"name": "the facilities desk", "rule": "seating, power and housekeeping requests"},
            {"name": "the travel desk", "rule": "domestic and international booking support with policy checks"},
        ],
        "patterns": [
            ("What is {name}?", "{name}: {rule}."),
            ("How do I access {name}?", "From the intranet home page under the relevant section."),
            ("Who owns {name}?", "Corporate Communications, except facility and travel services."),
            ("What is the SLA for {name} queries?", "2 business days for routine requests."),
        ],
    },
    {
        "domain": "GENERAL", "role": "employee", "product": "glossary", "freshness": "2026-09-05",
        "slots": [
            {"term": "CASA", "definition": "current account savings account, the low-cost deposit base of the bank"},
            {"term": "NPA", "definition": "non-performing asset, a loan overdue beyond 90 days"},
            {"term": "CRR", "definition": "cash reserve ratio, the share of deposits kept with the RBI"},
            {"term": "SLR", "definition": "statutory liquidity ratio, the share of deposits held in liquid assets"},
            {"term": "MCLR", "definition": "marginal cost of funds based lending rate"},
            {"term": "NIM", "definition": "net interest margin, interest income over interest-earning assets"},
            {"term": "UPI", "definition": "unified payments interface for instant account-to-account transfers"},
            {"term": "NEFT", "definition": "national electronic funds transfer in half-hourly batches"},
            {"term": "RTGS", "definition": "real-time gross settlement for high-value transfers"},
            {"term": "CTS", "definition": "cheque truncation system for image-based clearing"},
            {"term": "PEP", "definition": "politically exposed person requiring enhanced due diligence"},
            {"term": "STR", "definition": "suspicious transaction report filed with FIU-IND"},
            {"term": "VPN", "definition": "virtual private network for secure remote access"},
            {"term": "MFA", "definition": "multi-factor authentication combining a password with a second factor"},
            {"term": "CMDB", "definition": "configuration management database of production assets"},
            {"term": "PIR", "definition": "post-implementation review of a change"},
        ],
        "patterns": [
            ("What does {term} mean?", "{term} stands for {definition}."),
        ],
    },
    {
        "domain": "GENERAL", "role": "employee", "product": "service-standards", "freshness": "2026-09-10",
        "slots": [
            {"name": "IT incidents", "rule": "P1 within 2 hours, P2 within 8 hours, P3 within 2 business days"},
            {"name": "HR queries", "rule": "2 business days through the HR portal"},
            {"name": "compliance interpretations", "rule": "5 business days via the compliance desk"},
            {"name": "facilities requests", "rule": "next business day for routine requests"},
            {"name": "escalations", "rule": "missed SLAs escalate to the desk lead automatically"},
            {"name": "service feedback", "rule": "rate services through pulse surveys or ticket ratings"},
        ],
        "patterns": [
            ("What is the SLA for {name}?", "The SLA for {name}: {rule}."),
            ("How do I escalate {name}?", "Use the escalation contact directory for the owning desk."),
            ("How is {name} quality measured?", "Through closure confirmations and periodic surveys."),
            ("Where can I track {name}?", "In the ticketing system with the reference number."),
        ],
    },
    # ============================ CONVERSATIONAL_BI ============================
    {
        "domain": "CONVERSATIONAL_BI", "role": "analyst", "product": "bi-usage", "freshness": "2026-09-15",
        "slots": [
            {"name": "asking questions", "rule": "name the measure, dimensions and time window"},
            {"name": "data-as-of", "rule": "answers cite the model timestamp; verify against the dashboard"},
            {"name": "guardrails", "rule": "read-only queries, row limits and timeouts protect the warehouse"},
            {"name": "citations", "rule": "answers cite the semantic model and refresh time"},
            {"name": "bubble scope", "rule": "select the Conversational BI bubble for analytics questions"},
            {"name": "feedback", "rule": "rate answers to improve the assistant's BI accuracy"},
        ],
        "patterns": [
            ("What is the best practice for {name}?", "For {name}: {rule}."),
            ("Where do I learn {name}?", "The BI training guide and the data dictionary."),
            ("Who supports {name}?", "The Business Analytics CoE via the BI support queue."),
            ("What if my {name} fails?", "Rephrase with the measure and period, or raise a BI ticket."),
        ],
    },
    {
        "domain": "CONVERSATIONAL_BI", "role": "analyst", "product": "bi-metrics", "freshness": "2026-09-20",
        "slots": [
            {"name": "CASA ratio", "formula": "CASA deposits divided by total deposits", "owner": "Finance analytics"},
            {"name": "net interest margin", "formula": "net interest income over average interest-earning assets", "owner": "Finance analytics"},
            {"name": "cost-to-income", "formula": "operating expenses over operating income", "owner": "Finance analytics"},
            {"name": "credit cost", "formula": "provisions over average advances", "owner": "Risk analytics"},
            {"name": "digital adoption", "formula": "digital transactors over active customers", "owner": "Digital analytics"},
            {"name": "net promoter score", "formula": "promoters minus detractors from surveys", "owner": "Customer experience"},
        ],
        "patterns": [
            ("How is {name} calculated?", "The {name} is calculated as {formula}."),
            ("Who owns {name}?", "{owner} owns the definition and the dashboard."),
            ("Where can I see {name}?", "The executive dashboard, or ask the assistant for the trend."),
        ],
    },
    {
        "domain": "CONVERSATIONAL_BI", "role": "analyst", "product": "bi-access", "freshness": "2026-09-25",
        "slots": [
            {"name": "access requests", "rule": "route through the data access workflow with owner approval"},
            {"name": "roles", "rule": "viewer, analyst and advanced-analyst roles scope the toolset"},
            {"name": "row-level security", "rule": "geography, business and customer-tier dimensions filter data"},
            {"name": "training", "rule": "complete data literacy and conversational BI training first"},
            {"name": "certification", "rule": "analyst certification unlocks the advanced tools"},
            {"name": "audit", "rule": "all queries and exports are logged for review"},
        ],
        "patterns": [
            ("What is the process for {name}?", "For {name}: {rule}."),
            ("Who approves {name}?", "The data owner with the Data Governance team."),
            ("How long does {name} take?", "Standard approvals complete within 5 business days."),
        ],
    },
    {
        "domain": "CONVERSATIONAL_BI", "role": "analyst", "product": "bi-data", "freshness": "2026-09-30",
        "slots": [
            {"name": "freshness", "rule": "T0 within 15 minutes, T1 daily by 09:00 IST, T2 weekly or monthly"},
            {"name": "quality", "rule": "data-quality rules run at load and publish scores"},
            {"name": "lineage", "rule": "the data dictionary records source-to-metric lineage"},
            {"name": "ownership", "rule": "every metric has an owner and refresh timestamp"},
            {"name": "change control", "rule": "metric definition changes go through the KPI council"},
            {"name": "the dictionary", "rule": "the dictionary lists definitions, owners and caveats"},
        ],
        "patterns": [
            ("What is the policy on data {name}?", "The policy on data {name}: {rule}."),
            ("Where do I check {name}?", "The data quality dashboard or the data dictionary."),
            ("Who fixes {name} issues?", "The data engineering on-call, tracked to resolution."),
        ],
    },
    # ============================ AHA ============================
    {
        "domain": "AHA", "role": "employee", "product": "aha-points", "freshness": "2026-10-01",
        "slots": [
            {"name": "earning", "rule": "referrals, cross-sell wins, certifications and recognition earn points per the matrix"},
            {"name": "expiry", "rule": "points expire 24 months after award with 60-day dashboard warnings"},
            {"name": "reversal", "rule": "points reverse when the underlying transaction reverses"},
            {"name": "disputes", "rule": "raise disputes in the portal; the SLA is 5 business days"},
            {"name": "taxation", "rule": "redemptions may attract perquisite tax reflected in payroll"},
            {"name": "transfer", "rule": "points are non-transferable; giving to approved causes is supported"},
        ],
        "patterns": [
            ("What is the rule on point {name}?", "The rule on point {name}: {rule}."),
            ("Where do I see {name}?", "On the Aha dashboard under My Points."),
            ("Who handles {name}?", "The Rewards & Recognition team."),
            ("How do I raise a {name} request?", "Use the portal form with the transaction reference."),
        ],
    },
    {
        "domain": "AHA", "role": "employee", "product": "aha-redemption", "freshness": "2026-10-05",
        "slots": [
            {"name": "e-vouchers", "rule": "deliver instantly by email after checkout"},
            {"name": "merchandise", "rule": "ships in 7 to 10 business days to the registered address"},
            {"name": "experiences", "rule": "curated events with limited seats, first-come"},
            {"name": "giving", "rule": "donate points to approved causes with a receipt"},
            {"name": "exchanges", "rule": "e-vouchers are non-exchangeable once issued"},
            {"name": "delivery issues", "rule": "report within 7 days for redelivery or point credit"},
        ],
        "patterns": [
            ("How does {name} redemption work?", "For {name}: {rule}."),
            ("What is the SLA for {name}?", "Standard delivery timelines apply; disputes resolve in 5 business days."),
            ("Who do I contact about {name}?", "The Aha support desk through the portal."),
        ],
    },
    {
        "domain": "AHA", "role": "employee", "product": "aha-awards", "freshness": "2026-10-10",
        "slots": [
            {"name": "spot awards", "rule": "managers issue up to the quarterly cap with a citation"},
            {"name": "milestone awards", "rule": "granted at 5, 10, 15, 20 and 25 years of service"},
            {"name": "team of the quarter", "rule": "nominate with a delivery narrative and business-head endorsement"},
            {"name": "collaboration awards", "rule": "recognise cross-functional delivery with customer impact"},
            {"name": "approvals", "rule": "awards above the manager cap need the next-level approver"},
            {"name": "ceremonies", "rule": "awards present at town halls or regional events"},
        ],
        "patterns": [
            ("How do {name} work?", "For {name}: {rule}."),
            ("Who can nominate for {name}?", "Managers and peers through the portal, with endorsement rules."),
            ("How are {name} decided?", "A panel scores nominations on impact and collaboration."),
        ],
    },
    {
        "domain": "AHA", "role": "employee", "product": "aha-campaigns", "freshness": "2026-10-15",
        "slots": [
            {"name": "enrolment", "rule": "campaigns auto-track eligible actions unless stated"},
            {"name": "leaderboards", "rule": "optional standings published with consent"},
            {"name": "payout", "rule": "points credit within 30 days of campaign close"},
            {"name": "boosts", "rule": "limited-period multipliers on selected categories"},
            {"name": "eligibility", "rule": "eligibility follows the campaign brief"},
            {"name": "queries", "rule": "the campaign helpdesk responds within 3 business days"},
        ],
        "patterns": [
            ("How does campaign {name} work?", "For campaign {name}: {rule}."),
            ("Where do I track {name}?", "On the Aha campaign page."),
            ("Who resolves {name} issues?", "The Rewards & Recognition team."),
        ],
    },
    # ============================ AXIS_PHONE ============================
    {
        "domain": "AXIS_PHONE", "role": "contact-centre-agent", "product": "axis-phone-booking", "freshness": "2026-10-20",
        "slots": [
            {"name": "slot booking", "rule": "30-minute slots between 09:00 and 20:00 IST over the next five working days"},
            {"name": "confirmation", "rule": "an SMS confirms the slot with a callback reference ID"},
            {"name": "rescheduling", "rule": "reschedule up to 30 minutes before the slot"},
            {"name": "cancellation", "rule": "cancel via the app or the SMS link; slots free up for other customers"},
            {"name": "missed callbacks", "rule": "one automatic retry, then supervisor follow-up"},
            {"name": "no-shows", "rule": "customers can rebook without penalty"},
        ],
        "patterns": [
            ("How does {name} work?", "For {name}: {rule}."),
            ("Where can customers manage {name}?", "The mobile app, internet banking or the assistant."),
            ("What is the SLA around {name}?", "Priority within 15 minutes of the slot; retail within 60 minutes."),
            ("How do I handle a {name} query?", "Use the agent console and the booking playbook."),
        ],
    },
    {
        "domain": "AXIS_PHONE", "role": "contact-centre-agent", "product": "axis-phone-routing", "freshness": "2026-10-22",
        "slots": [
            {"name": "topic routing", "rule": "accounts, cards, loans, wealth and complaints route to topic queues"},
            {"name": "language preference", "rule": "captured at booking and honoured in routing"},
            {"name": "priority handling", "rule": "Priority and Burgundy customers use dedicated queues"},
            {"name": "the IVR tree", "rule": "language, service, authentication, then queue"},
            {"name": "transfers", "rule": "warm transfers preserve context; cold transfers need supervisor approval for priority"},
            {"name": "repeat callers", "rule": "routed to the same agent when available"},
        ],
        "patterns": [
            ("How does {name} work?", "For {name}: {rule}."),
            ("Who configures {name}?", "Contact Centre Technology with the Assisted Channels team."),
            ("What if {name} fails?", "Escalate to the routing support queue and log the interaction ID."),
        ],
    },
    {
        "domain": "AXIS_PHONE", "role": "contact-centre-agent", "product": "axis-phone-service", "freshness": "2026-10-24",
        "slots": [
            {"name": "disposition codes", "rule": "every call ends with a code and a CRM summary"},
            {"name": "wrap-up", "rule": "complete within the defined wrap-up time before the next interaction"},
            {"name": "scripts", "rule": "mandatory scripts apply to disclosures and verifications"},
            {"name": "recording", "rule": "calls are recorded for quality and compliance"},
            {"name": "the agent console", "rule": "shows the customer card and interaction history"},
            {"name": "etiquette", "rule": "greet with name and bank, verify identity, confirm actions"},
        ],
        "patterns": [
            ("What is the standard for {name}?", "The standard for {name}: {rule}."),
            ("Who audits {name}?", "Quality assurance samples calls and scores against the rubric."),
            ("Where do I find {name} guidance?", "The contact-centre playbook on the intranet."),
        ],
    },
    {
        "domain": "AXIS_PHONE", "role": "contact-centre-agent", "product": "axis-phone-quality", "freshness": "2026-10-26",
        "slots": [
            {"name": "the CSAT survey", "rule": "an SMS survey follows every completed call and callback"},
            {"name": "quality audits", "rule": "sampled calls are scored monthly against the rubric"},
            {"name": "coaching", "rule": "scores feed coaching plans with team leads"},
            {"name": "calibration", "rule": "monthly sessions align auditor scoring"},
            {"name": "the detractor loop", "rule": "detractors receive follow-up within 48 hours"},
            {"name": "targets", "rule": "channel CSAT targets are set quarterly"},
        ],
        "patterns": [
            ("How does {name} work?", "For {name}: {rule}."),
            ("Who owns {name}?", "The Assisted Channels quality team."),
            ("How do I improve on {name}?", "Review audit scores and complete coaching actions."),
        ],
    },
    # ============================ DOWNLOAD ============================
    {
        "domain": "DOWNLOAD", "role": "employee", "product": "download-portal", "freshness": "2026-10-27",
        "slots": [
            {"name": "search", "rule": "search by form name, code or process; results show version and owner"},
            {"name": "watermarking", "rule": "downloaded PDFs watermark with the employee ID"},
            {"name": "versions", "rule": "only the latest version is served; older versions are archived"},
            {"name": "form requests", "rule": "new forms route through the owning team with governance review"},
            {"name": "mobile access", "rule": "the portal works on managed mobile devices via the intranet"},
            {"name": "feedback", "rule": "report form errors through the portal feedback link"},
        ],
        "patterns": [
            ("How does {name} work on the portal?", "For {name}: {rule}."),
            ("Who supports {name}?", "Corporate Communications with the owning department."),
            ("What if {name} fails?", "Raise a portal ticket; the SLA is 2 business days."),
            ("Where do I learn {name}?", "The portal user guide."),
        ],
    },
    {
        "domain": "DOWNLOAD", "role": "employee", "product": "forms", "freshness": "2026-10-28",
        "slots": [
            {"name": "HR-LEAVE-01", "note": "special leave application with manager approval"},
            {"name": "HR-TRVL-01", "note": "travel expense statement with receipts"},
            {"name": "IT-SW-01", "note": "new software request with justification"},
            {"name": "KYC-INDV-01", "note": "individual KYC application with Officially Valid Documents"},
            {"name": "FIN-VEND-01", "note": "new vendor setup with bank details and GST"},
            {"name": "GRV-01", "note": "customer grievance form with resolution notes"},
        ],
        "patterns": [
            ("What is {name} used for?", "The form {name} is the {note}."),
            ("Where do I submit {name}?", "Through the owning system per the form instructions."),
            ("What version of {name} is valid?", "Only the latest version on the portal is valid."),
        ],
    },
    {
        "domain": "DOWNLOAD", "role": "employee", "product": "submissions", "freshness": "2026-10-28",
        "slots": [
            {"name": "validation", "rule": "forms validate mandatory fields before submission"},
            {"name": "rejection", "rule": "rejections state the reason; correct and resubmit"},
            {"name": "routing", "rule": "submissions route to the owning team automatically"},
            {"name": "status tracking", "rule": "track status with the submission reference"},
            {"name": "SLA", "rule": "owning teams respond per their service standards"},
            {"name": "evidence", "rule": "attach supporting documents in the accepted formats"},
        ],
        "patterns": [
            ("How does submission {name} work?", "For submission {name}: {rule}."),
            ("Who handles {name}?", "The owning team of the form."),
            ("What if {name} breaks?", "Raise a portal ticket with the submission reference."),
        ],
    },
]


def _generate_faqs() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for topic in FAQ_TOPICS:
        for slot in topic["slots"]:
            for q_tpl, a_tpl in topic["patterns"]:
                question = q_tpl.format(**slot).strip()
                if question in seen:
                    continue
                seen.add(question)
                rows.append({
                    "question": question,
                    "answer": a_tpl.format(**slot).strip(),
                    "domain": topic["domain"],
                    "role": topic["role"],
                    "product": topic["product"],
                    "freshness": topic["freshness"],
                })
    return rows


def _write_faqs() -> None:
    original: list[dict] = []
    if FAQS_CSV.exists():
        with FAQS_CSV.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            original = [row for row in reader if row.get("question")]
    generated = _generate_faqs()
    seen = {row["question"].strip() for row in original}
    added = [row for row in generated if row["question"] not in seen]
    merged = original + added
    with FAQS_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["question", "answer", "domain", "role", "product", "freshness"]
        )
        writer.writeheader()
        writer.writerows(merged)
    print(f"FAQs: {len(original)} original + {len(added)} generated = {len(merged)} total")


# ---------------------------------------------------------------------------
# Document generation
# ---------------------------------------------------------------------------

def _build_docs() -> list[dict]:
    docs: list[dict] = []

    # ------------------------------ HR ------------------------------
    roles = [
        ("Relationship Manager", "rm", "customer relationships"),
        ("Teller", "teller", "cash and counter services"),
        ("Credit Officer", "credit", "underwriting and appraisals"),
        ("Branch Ops Head", "opshead", "branch operations and controls"),
        ("Contact Centre Agent", "ccagent", "phone and chat servicing"),
        ("HR Business Partner", "hrbp", "people advisory for business units"),
        ("Compliance Officer", "compoff", "regulatory adherence"),
        ("Data Analyst", "analyst", "reports and dashboards"),
        ("IT Support Engineer", "itsupport", "endpoint and service desk"),
        ("Digital Product Manager", "dpm", "digital journeys"),
        ("Collection Officer", "collect", "delinquency follow-up"),
        ("Wealth Manager", "wealth", "advisory for affluent clients"),
    ]
    for name, short, focus in roles:
        docs.append({
            "bubble": "HR", "slug": f"role_playbook_{short}",
            "title": f"Role Playbook: {name}",
            "body": _body([
                ("Role Summary", [
                    f"The {name} is accountable for {focus}. This playbook summarises the "
                    "core responsibilities, tools, policies and measures that apply to the role.",
                ]),
                ("Core Responsibilities", [
                    "Deliver the defined outcomes for the role within service standards.",
                    "Follow the applicable operating procedures and checklists without shortcuts.",
                    "Escalate risks, exceptions and customer-impacting issues to the team lead.",
                ]),
                ("Tools & Systems", [
                    "Core banking and CRM systems provisioned per the role profile.",
                    "The intranet knowledge portal and the वार्तालाप assistant for policy lookup.",
                    "The learning management system for mandatory and role-based training.",
                ]),
                ("Key Policies", [
                    "Code of Conduct, information security and data privacy policies.",
                    "Attendance, leave and reimbursement policies per the HR intranet.",
                    "Role-specific compliance policies as listed in the onboarding checklist.",
                ]),
                ("Metrics & Reviews", [
                    "Role KPIs are set during goal setting and reviewed mid-year and annually.",
                    "Quality assurance and audit observations are part of the scorecard.",
                ]),
                ("Policy code", [f"HR-RPB-{short.upper()}-2026-01 | Owner: HR Operations."]),
            ]),
        })

    units = [
        ("Retail Banking", "retail", "March year-end and festival surges"),
        ("Branch Operations", "bops", "month-end and regulatory reporting peaks"),
        ("Contact Centre", "cc", "campaign and incident-driven spikes"),
        ("Digital Channels", "digital", "release and sale events"),
        ("Cards", "cards", "statement cycle and campaign peaks"),
        ("Payments", "payments", "festival transaction surges"),
        ("Wealth Management", "wm", "quarter-end portfolio reviews"),
        ("SME Banking", "sme", "quarter-end disbursement pushes"),
        ("Wholesale Banking", "ws", "deal-closure cycles"),
        ("Risk", "risk", "month-end reporting peaks"),
        ("Technology", "tech", "release and change-freeze windows"),
        ("HR Operations", "hrops", "appraisal and year-end cycles"),
    ]
    for name, short, peak in units:
        docs.append({
            "bubble": "HR", "slug": f"leave_planning_{short}",
            "title": f"{name} Leave Planning Guide 2026",
            "body": _body([
                ("Purpose", [
                    f"This guide helps {name} teams plan leave without compromising "
                    f"coverage during peak periods such as {peak}.",
                ]),
                ("Planning Rules", [
                    "Privileged leave needs at least 7 working days of notice and manager approval.",
                    "At least 70 percent of the team must be available during declared peak windows.",
                    "Backfill plans must be agreed before overlapping leave is approved.",
                ]),
                ("Seasonal Guidance", [
                    f"Anticipate demand around {peak} and open early leave planning.",
                    "Rotate preferred holiday weeks across the team from year to year.",
                ]),
                ("Manager Duties", [
                    "Publish the unit leave calendar quarterly.",
                    "Review pending balances and prompt planned usage.",
                    "Escalate conflicts to the HR business partner.",
                ]),
                ("Policy code", [f"HR-LVG-{short.upper()}-2026-01 | Owner: HR Operations."]),
            ]),
        })

    processes = [
        ("Leave Approval", "leave", "HR portal > Leave > Apply"),
        ("Reimbursement Claim", "reimb", "HR portal > Pay > Reimbursements"),
        ("IJP Application", "ijp", "Careers portal > Internal Jobs"),
        ("Performance Goal Setting", "goals", "Performance module > Goal Setting"),
        ("Exit Clearance", "exit", "HR portal > Separation > Clearance"),
        ("Attendance Regularisation", "att", "HR portal > Attendance > Regularise"),
        ("Insurance Enrolment", "ins", "HR portal > Benefits > Enrolment"),
        ("L&D Nomination", "lnd", "LMS > External Programmes"),
        ("Transfer Request", "trf", "HR portal > Career > Transfer"),
        ("Promotion Review", "promo", "Performance module > Promotion"),
        ("Referral Submission", "ref", "Careers portal > Refer a Friend"),
        ("Grievance Filing", "grv", "HR portal > Grievances > File"),
    ]
    for name, short, entry in processes:
        docs.append({
            "bubble": "HR", "slug": f"checklist_{short}",
            "title": f"Process Checklist: {name}",
            "body": _body([
                ("Entry Point", [f"Start the process from {entry}."]),
                ("Checklist", [
                    "1. Confirm eligibility per the policy before starting.",
                    "2. Prepare the supporting documents listed in the form.",
                    "3. Obtain the required manager or HR approvals.",
                    "4. Submit and note the reference number.",
                    "5. Track the request and respond to queries within 2 business days.",
                ]),
                ("Common Rejections", [
                    "Missing documents, incomplete fields, or approvals outside the authority matrix.",
                ]),
                ("SLA", ["Standard requests complete within 5 business days unless the policy states otherwise."]),
                ("Policy code", [f"HR-CHK-{short.upper()}-2026-01 | Owner: HR Operations."]),
            ]),
        })

    policies = [
        ("Leave Policy", "leave", "24 PL, 8 CL, 12 SL per calendar year", "HR-LEAVE-2026-01"),
        ("Travel Policy", "travel", "approval-based domestic and international travel", "HR-TRVL-2026-01"),
        ("Reimbursement Policy", "reimb", "monthly claims by the 5th with receipts", "HR-REIMB-2026-01"),
        ("Dress Code", "dress", "business formals for customer-facing roles", "HR-DRESS-2026-01"),
        ("Code of Conduct", "coc", "integrity, confidentiality and fair dealing", "HR-COC-2026-01"),
        ("POSH Policy", "posh", "zero-tolerance harassment policy with ICC process", "HR-POSH-2026-01"),
        ("Social Media Policy", "social", "no unapproved brand statements", "HR-SM-2026-01"),
        ("Data Privacy Policy", "priv", "need-to-know access to employee data", "HR-PRIV-2026-01"),
        ("Attendance Policy", "att", "biometric attendance with regularisation", "HR-ATT-2026-01"),
        ("Flexible Work Policy", "flex", "up to 2 WFH days per week", "HR-FLEX-2026-01"),
        ("Relocation Policy", "reloc", "scheduled support for bank-initiated moves", "HR-RELOC-2026-01"),
        ("Recognition Policy", "recog", "spot, milestone and team awards", "HR-RECOG-2026-01"),
    ]
    for name, short, facts, code in policies:
        docs.append({
            "bubble": "HR", "slug": f"quickref_{short}",
            "title": f"Quick Reference: {name}",
            "body": _body([
                ("In One Line", [facts + "."]),
                ("Where to Find", ["The full policy is on the HR intranet under Policies > Employee."]),
                ("Approvals", ["Exceptions need the reporting manager and HR business partner."]),
                ("Breach", ["Non-compliance is addressed under the disciplinary process."]),
                ("Policy code", [f"{code} | Owner: HR Operations."]),
            ]),
        })

    # ------------------------------ IT_HELPDESK ------------------------------
    services = [
        ("VPN Access", "vpn"), ("Email & Mailbox", "email"), ("Laptop Support", "laptop"),
        ("Printer Support", "printer"), ("Video-Conference Rooms", "vcroom"),
        ("Software Installation", "software"), ("Office Wi-Fi", "wifi"),
        ("Remote Desktop", "rdp"), ("Shared Mailbox", "sharedmb"),
        ("MFA & Identity", "mfa"), ("Asset Tagging", "asset"), ("Data Backup", "backup"),
    ]
    for name, short in services:
        docs.append({
            "bubble": "IT_HELPDESK", "slug": f"service_guide_{short}",
            "title": f"Service Guide: {name}",
            "body": _body([
                ("What This Service Covers", [
                    f"End-to-end support for {name}: requests, incidents and guidance.",
                ]),
                ("How to Request", [
                    "Raise a Unidesk ticket under IT Helpdesk with the employee ID and asset details.",
                    "Self-service options are available in the service catalogue where applicable.",
                ]),
                ("Service Hours", [
                    "Standard support: 09:00 to 18:00 IST on working days.",
                    "Critical incidents: 24x7 through the security and operations desks.",
                ]),
                ("Escalation", [
                    "Escalate SLA breaches to the desk lead, then the IT service manager.",
                ]),
                ("Policy code", [f"IT-SVC-{short.upper()}-2026-01 | Owner: IT Service Management."]),
            ]),
        })

    systems = [
        ("Unidesk", "unidesk", "ticketing and service requests"),
        ("Active Directory", "ad", "identity and access"),
        ("Microsoft Teams", "teams", "chat and meetings"),
        ("SharePoint", "sharepoint", "team sites and documents"),
        ("OneDrive", "onedrive", "personal file storage"),
        ("Endpoint Agent", "edr", "device security and patching"),
        ("Print Server", "print", "network printing"),
        ("VPN Gateway", "vpn", "remote connectivity"),
        ("Meeting Room Devices", "vc", "room video hardware"),
        ("Identity Portal", "idp", "password and MFA self-service"),
        ("Antivirus Console", "av", "malware protection"),
        ("Patching System", "patch", "monthly updates"),
    ]
    for name, short, purpose in systems:
        docs.append({
            "bubble": "IT_HELPDESK", "slug": f"access_guide_{short}",
            "title": f"Access Request Guide: {name}",
            "body": _body([
                ("System Purpose", [f"{name} provides {purpose}."]),
                ("Access Levels", [
                    "Standard user access maps to the role profile.",
                    "Elevated or administrator access requires additional justification.",
                ]),
                ("Request Flow", [
                    "1. Raise the request in Unidesk under IT Helpdesk > Access.",
                    "2. Reporting manager approves.",
                    "3. InfoSec reviews for privileged access.",
                    "4. Provisioning completes within 2 business days.",
                ]),
                ("Reviews", ["Access is reviewed quarterly with the system owner."]),
                ("Policy code", [f"IT-ACC-{short.upper()}-2026-01 | Owner: Identity & Access Management."]),
            ]),
        })

    for name, short in services:
        docs.append({
            "bubble": "IT_HELPDESK", "slug": f"sla_sheet_{short}",
            "title": f"SLA & Escalation Sheet: {name}",
            "body": _body([
                ("Severity Definitions", [
                    f"P1: {name} unavailable for the whole team or a critical business area.",
                    f"P2: significant degradation affecting part of the {name} service.",
                    "P3: single-user issue with a workaround available.",
                ]),
                ("Response Targets", [
                    "P1: response within 30 minutes, resolution within 2 hours.",
                    "P2: response within 2 hours, resolution within 8 hours.",
                    "P3: response within 4 business hours, resolution within 2 business days.",
                ]),
                ("Escalation Chain", [
                    "1. Service desk (first point of contact).",
                    "2. Desk lead for SLA breaches.",
                    "3. IT service manager and the business owner for P1 events.",
                ]),
                ("Reporting", ["SLA performance publishes on the monthly service dashboard."]),
                ("Policy code", [f"IT-SLA-{short.upper()}-2026-01 | Owner: IT Service Management."]),
            ]),
        })

    # ------------------------------ LAW ------------------------------
    regulations = [
        ("PMLA", "pmla", "anti-money-laundering obligations including STR/CTR filing and record retention"),
        ("KYC Master Direction", "kyc", "customer identification, verification and periodic updation"),
        ("DPDP Act", "dpdp", "consent, breach notification and data principal rights"),
        ("IT Act 2000", "itact", "electronic records, cyber security and incident reporting"),
        ("Negotiable Instruments Act", "niact", "cheques, dishonour and payment in due course"),
        ("SARFAESI", "sarfaesi", "enforcement of security interest for secured creditors"),
        ("FEMA", "fema", "current and capital account transactions and reporting"),
        ("DICGC Scheme", "dicgc", "deposit insurance up to the prescribed ceiling"),
        ("Payment & Settlement Systems Act", "pss", "authorised payment systems and customer protection"),
        ("Consumer Protection Act", "cpa", "service deficiency and unfair contract terms"),
        ("Banking Ombudsman Scheme", "ombud", "free grievance resolution for unresolved complaints"),
        ("RBI Cyber Framework", "cyber", "security operations, VAPT and board oversight"),
    ]
    for name, short, digest in regulations:
        docs.append({
            "bubble": "LAW", "slug": f"digest_{short}",
            "title": f"Staff Digest: {name}",
            "body": _body([
                ("What It Governs", [digest + "."]),
                ("Bank Application", [
                    "The owning team translates the framework into internal policies and procedures.",
                    "Staff must follow the internal procedure even where it is stricter than the statute.",
                ]),
                ("Practical Reminders", [
                    "Keep the latest internal circular handy for day-to-day decisions.",
                    "Escalate interpretation questions to the compliance desk.",
                    "Preserve records for the retention period; never alter audit trails.",
                ]),
                ("Where to Read More", [
                    "The compliance intranet summarises applicability; the full text is on the regulator's site.",
                ]),
                ("Policy code", [f"LAW-DG-{short.upper()}-2026-01 | Owner: Compliance."]),
            ]),
        })

    checklists = [
        ("Account Opening", "acctopen", "KYC documents, risk category and beneficial ownership"),
        ("Video KYC", "vkyp", "geo-tagging, liveness and consent capture"),
        ("STR Filing", "str", "suspicion narrative, transaction detail and timelines"),
        ("Vendor Onboarding", "vend", "due diligence, sanctions screening and contract clauses"),
        ("Record Retention", "ret", "classes, schedules and litigation holds"),
        ("Legal Hold", "hold", "custodians, scope and release"),
        ("Subpoena Response", "subp", "intake, ownership and deadlines"),
        ("Gift Register", "gift", "declarations, thresholds and approvals"),
        ("Insider Trading Disclosures", "insider", "designated persons and trading windows"),
        ("Call Monitoring", "callmon", "recording disclosure, storage and usage"),
        ("Grievance Handling", "grv", "acknowledgement, resolution and escalation"),
        ("Outsourcing Review", "outs", "materiality, audits and exit clauses"),
    ]
    for name, short, scope in checklists:
        docs.append({
            "bubble": "LAW", "slug": f"checklist_{short}",
            "title": f"Compliance Checklist: {name}",
            "body": _body([
                ("Scope", [f"This checklist covers {scope}."]),
                ("Steps", [
                    "1. Confirm the applicable policy version before starting.",
                    "2. Complete each control in order; note exceptions explicitly.",
                    "3. Attach evidence: documents, screenshots or approvals.",
                    "4. Obtain the required compliance sign-off.",
                    "5. Retain the completed checklist per the retention schedule.",
                ]),
                ("Common Gaps", [
                    "Missing evidence, outdated policy versions and skipped approvals.",
                ]),
                ("Escalation", ["Unresolvable gaps escalate to the compliance desk same-day."]),
                ("Policy code", [f"LAW-CL-{short.upper()}-2026-01 | Owner: Compliance."]),
            ]),
        })

    advisories = [
        ("High-value cash deposit", "cashdep", "Large cash credits must be reconciled with the declared business profile and escalated where inconsistent."),
        ("Suspicious structuring", "struct", "Split deposits designed to stay under reporting thresholds are a classic red flag."),
        ("Data subject request", "dsr", "Access and erasure requests carry statutory timelines and need the privacy desk's coordination."),
        ("Regulator notice", "regnotice", "Regulatory requisitions route through legal intake with strict internal deadlines."),
        ("Cheque dishonour dispute", "cheque", "Dishonour handling must follow the NI Act process, including return memos and customer communication."),
        ("Cross-border remittance query", "femaq", "Remittance queries need FEMA purpose codes and the authorised dealer process."),
        ("Media query", "media", "Media queries are handled only by Corporate Communications; staff must not comment."),
        ("Recovery agent complaint", "recovery", "Recovery interactions follow the fair practices code; complaints escalate to the nodal officer."),
        ("Social media leak", "smleak", "Suspect posts about the bank are reported to security and communications immediately."),
        ("Third-party breach", "tpbreach", "Vendor-side breaches activate the incident playbook and contractual notification timelines."),
    ]
    for name, short, guidance in advisories:
        docs.append({
            "bubble": "LAW", "slug": f"advisory_{short}",
            "title": f"Advisory: {name}",
            "body": _body([
                ("Situation", [f"A {name} situation has been reported or detected."]),
                ("Key Considerations", [guidance]),
                ("Immediate Steps", [
                    "1. Preserve all evidence in its current state.",
                    "2. Inform the owning team and the compliance or legal desk.",
                    "3. Do not communicate externally without approval.",
                ]),
                ("Escalation", ["Escalate to the relevant officer within the same business day."]),
                ("Policy code", [f"LAW-ADV-{short.upper()}-2026-01 | Owner: Legal & Compliance."]),
            ]),
        })

    for name, short, digest in regulations[:10]:
        docs.append({
            "bubble": "LAW", "slug": f"faqsheet_{short}",
            "title": f"Quick FAQ Sheet: {name}",
            "body": _body([
                ("Frequently Asked", [
                    f"Q: Where does {name} apply?",
                    f"A: {digest}.",
                    "Q: Who do I ask for interpretation?",
                    "A: The compliance desk owns interpretation; follow their written guidance.",
                    "Q: Where is the internal procedure?",
                    "A: The compliance intranet under Regulations > Current.",
                    "Q: What if I miss a deadline?",
                    "A: Report immediately; late actions are a compliance breach.",
                ]),
                ("Policy code", [f"LAW-FS-{short.upper()}-2026-01 | Owner: Compliance."]),
            ]),
        })

    # ------------------------------ FINANCIAL_ADVISOR ------------------------------
    products = [
        ("Savings Accounts", "savings", "daily-balance interest and variant-based value adds"),
        ("Current Accounts", "current", "business banking with cash management"),
        ("Credit Cards", "cards", "rewards, cashback and travel variants"),
        ("Personal Loans", "pl", "unsecured credit for salaried and self-employed"),
        ("Home Loans", "hl", "purchase, construction and balance transfer"),
        ("Car Loans", "cl", "new, pre-owned and electric vehicle funding"),
        ("Education Loans", "el", "domestic and international course funding"),
        ("Gold Loans", "gl", "quick secured credit against ornaments"),
        ("Fixed & Recurring Deposits", "deposits", "term deposits with flexible interest payouts"),
        ("Small Savings Schemes", "sss", "PPF, NPS, Sukanya and SCSS"),
    ]
    for name, short, blurb in products:
        docs.append({
            "bubble": "FINANCIAL_ADVISOR", "slug": f"product_note_{short}",
            "title": f"Product Note: {name}",
            "body": _body([
                ("Overview", [f"{name} serve customers with {blurb}."]),
                ("Key Features", [
                    "Features and limits are as per the current product master.",
                    "Interest, fees and charges follow the published tariff.",
                ]),
                ("Advisory Cues", [
                    "Confirm the latest variant details before quoting to customers.",
                    "Explain fees and charges in plain language.",
                    "Document customer decisions and consent.",
                ]),
                ("Support", ["Product queries route to the product helpdesk via the CRM."]),
                ("Policy code", [f"FA-NOTE-{short.upper()}-2026-01 | Owner: Products & Advisory."]),
            ]),
        })
        docs.append({
            "bubble": "FINANCIAL_ADVISOR", "slug": f"eligibility_{short}",
            "title": f"Eligibility & Documents: {name}",
            "body": _body([
                ("Eligibility", [
                    "Eligibility follows the product policy: age, income, credit and relationship criteria.",
                    "Co-applicants and guarantors are governed by the product rules.",
                ]),
                ("Documents", [
                    "KYC: Officially Valid Documents plus PAN or Form 60.",
                    "Income proof as per the product checklist.",
                    "Purpose or security documents for secured products.",
                ]),
                ("Verification", [
                    "Verify documents at origination and re-verify per policy.",
                ]),
                ("Rejections", ["Rejections state the policy clause; refer to the credit desk for appeals."]),
                ("Policy code", [f"FA-ELIG-{short.upper()}-2026-01 | Owner: Products & Advisory."]),
            ]),
        })
        docs.append({
            "bubble": "FINANCIAL_ADVISOR", "slug": f"conv_guide_{short}",
            "title": f"Customer Conversation Guide: {name}",
            "body": _body([
                ("Opening", [
                    "Understand the customer's need and time horizon before proposing anything.",
                    "Ask about current holdings and preferences.",
                ]),
                ("Explaining", [
                    "Use the approved one-pager for {name}.",
                    "State features, charges and limitations in plain language.",
                ]),
                ("Closing", [
                    "Summarise what was discussed and agreed.",
                    "Record consent and next steps in the CRM.",
                ]),
                ("Guardrails", [
                    "No promises beyond documented features.",
                    "Route suitability questions to the risk-profiling framework.",
                ]),
                ("Policy code", [f"FA-CONV-{short.upper()}-2026-01 | Owner: Products & Advisory."]),
            ]),
        })

    for period in ["October 2026", "November 2026", "December 2026", "January 2027"]:
        short = period.split()[0].lower() + period.split()[1]
        docs.append({
            "bubble": "FINANCIAL_ADVISOR", "slug": f"rate_review_{short}",
            "title": f"Rate & Product Review Note: {period}",
            "body": _body([
                ("Purpose", [
                    f"This note summarises product and rate positioning guidance for {period}.",
                ]),
                ("Guidance", [
                    "Quote only published rates; internal indicative rates are not customer-facing.",
                    "Highlight scheme-linked products where the customer is eligible.",
                ]),
                ("Conversation Themes", [
                    "Deposit ladders for rate-sensitive customers.",
                    "Home loan balance transfer conversations for existing borrowers.",
                    "Festival offers with documented terms.",
                ]),
                ("Compliance", ["All communications must use approved creatives and disclosures."]),
                ("Policy code", [f"FA-RATE-{short.upper()}-2026-01 | Owner: Products & Advisory."]),
            ]),
        })

    # ------------------------------ CR ------------------------------
    cr_systems = [
        ("Core Banking", "cbs"), ("Internet Banking", "inb"), ("Mobile App", "mob"),
        ("Payments Switch", "pay"), ("CRM", "crm"), ("Lending System", "lend"),
        ("Cards Platform", "cards"), ("ATM Network", "atm"), ("IVR", "ivr"),
        ("BI Platform", "bi"), ("Data Warehouse", "dwh"),
    ]
    for name, short in cr_systems:
        docs.append({
            "bubble": "CR", "slug": f"runbook_{short}",
            "title": f"Runbook: {name} Deployment",
            "body": _body([
                ("Pre-Checks", [
                    "Confirm the change ID, window and rollback plan.",
                    "Verify backups and monitoring dashboards are green.",
                ]),
                ("Execution", [
                    "1. Announce the deployment in the change channel.",
                    "2. Apply the change per the approved steps.",
                    "3. Run smoke checks and compare against the baseline.",
                ]),
                ("Verification", [
                    "Validate key journeys and batch jobs for the defined observation period.",
                ]),
                ("Rollback", [
                    "If smoke checks fail, trigger rollback and notify the service desk immediately.",
                ]),
                ("Policy code", [f"CR-RUN-{short.upper()}-2026-01 | Owner: Release Management."]),
            ]),
        })

    cr_types = [
        ("Standard Configuration", "config"), ("Certificate Renewal", "cert"),
        ("Server Patching", "patch"), ("Hotfix", "hotfix"), ("Feature Release", "feature"),
        ("Infrastructure Migration", "migrate"), ("Database Schema", "dbschema"),
        ("Firewall Rule", "fw"), ("Capacity Add", "capacity"), ("Decommissioning", "decom"),
        ("Batch Rerun", "batch"),
    ]
    for name, short in cr_types:
        docs.append({
            "bubble": "CR", "slug": f"walkthrough_{short}",
            "title": f"Walkthrough: {name} Change",
            "body": _body([
                ("When This Applies", [f"A {name} change is planned, covering defined components only."]),
                ("Step-by-Step", [
                    "1. Draft the CR with impact assessment and the risk score.",
                    "2. Attach test evidence and the rollback plan.",
                    "3. Obtain approvals per the matrix.",
                    "4. Implement inside the approved window.",
                    "5. Complete the post-implementation review.",
                ]),
                ("Watch Points", [
                    "No scope expansion inside the window.",
                    "Incident linkage is mandatory for production changes.",
                ]),
                ("Policy code", [f"CR-WALK-{short.upper()}-2026-01 | Owner: Change Management Office."]),
            ]),
        })

    for month in ["October", "November", "December", "January", "February", "March"]:
        short = month.lower()
        docs.append({
            "bubble": "CR", "slug": f"cab_agenda_{short}",
            "title": f"CAB Agenda Template: {month} 2026-27",
            "body": _body([
                ("Standing Items", [
                    "Review of the previous meeting minutes and actions.",
                    "Emergency change retrospectives.",
                    "Change calendar review for the coming two weeks.",
                ]),
                ("Approvals", [
                    "Medium-risk changes with business representation.",
                    "High-risk changes with business head participation.",
                ]),
                ("Metrics Review", [
                    "Success rate, emergency ratio, PIR completion and freeze adherence.",
                ]),
                ("Open Risks", ["Changes returning from review and blocked items."]),
                ("Policy code", [f"CR-CABAG-{short.upper()}-2026-01 | Owner: Change Management Office."]),
            ]),
        })

    for name, short, detail in [
        ("Financial Year-End", "ye", "last 5 business days of March"),
        ("Half-Year Close", "hy", "last 3 business days of September"),
        ("Diwali Sale Period", "diwali", "5 days around the festival sale"),
        ("New Year Window", "ny", "31 December to 2 January"),
        ("RBI Reporting Window", "rbi", "regulatory filing days"),
    ]:
        docs.append({
            "bubble": "CR", "slug": f"freeze_note_{short}",
            "title": f"Change Freeze Note: {name}",
            "body": _body([
                ("Freeze Window", [f"The {name} freeze covers {detail}."]),
                ("Applicability", [
                    "All production changes need a freeze exception during the window.",
                    "Customer-facing systems are fully frozen; internal systems follow the calendar.",
                ]),
                ("Exceptions", [
                    "Exceptions route as emergency changes with CIO approval.",
                    "Incident remediation is always permitted.",
                ]),
                ("Preparation", [
                    "Complete planned changes before the freeze starts.",
                    "Confirm rollback readiness and on-call rosters.",
                ]),
                ("Policy code", [f"CR-FZ-{short.upper()}-2026-01 | Owner: Change Management Office."]),
            ]),
        })

    # ------------------------------ GENERAL ------------------------------
    depts = [
        ("Branch Banking", "branch", "counter services, KYC and customer handling"),
        ("Contact Centre", "cc", "callbacks, complaints and servicing"),
        ("Digital Channels", "digital", "app, internet banking and journeys"),
        ("Cards", "cards", "acquisition, spends and disputes"),
        ("Payments", "payments", "UPI, NEFT/RTGS and mandates"),
        ("Wealth Management", "wm", "advisory and relationship coverage"),
        ("SME Banking", "sme", "business banking and working capital"),
        ("Wholesale Banking", "ws", "corporate relationships and trade"),
        ("Risk", "risk", "credit, market and operational risk"),
        ("Compliance", "compliance", "regulatory adherence and advisory"),
        ("Technology", "tech", "engineering, operations and security"),
        ("HR Operations", "hr", "employee services and lifecycle"),
    ]
    for name, short, focus in depts:
        docs.append({
            "bubble": "GENERAL", "slug": f"dept_onboarding_{short}",
            "title": f"{name} Onboarding Guide",
            "body": _body([
                ("Welcome", [f"This guide helps new joiners in {name} get productive quickly."]),
                ("What The Department Does", [f"{name} owns {focus}."]),
                ("Your First Week", [
                    "Complete mandatory e-learning: code of conduct, security and AML.",
                    "Meet the team lead and the buddy.",
                    "Explore the department's knowledge base on the intranet.",
                ]),
                ("Systems To Know", [
                    "Core systems are provisioned per the role profile.",
                    "The वार्तालाप assistant answers policy and process questions.",
                ]),
                ("Who To Ask", ["Team lead for work, HRBP for people matters, IT helpdesk for systems."]),
                ("Policy code", [f"GEN-ONB-{short.upper()}-2026-01 | Owner: Learning & Development."]),
            ]),
        })
        docs.append({
            "bubble": "GENERAL", "slug": f"dept_metrics_{short}",
            "title": f"{name} Metrics Handbook",
            "body": _body([
                ("Purpose", [f"Defines the metrics that {name} tracks to manage performance."]),
                ("Core Metrics", [
                    "Volume, quality, turnaround and customer experience measures per the scorecard.",
                    "Compliance and audit metrics where the department owns controls.",
                ]),
                ("Cadence", [
                    "Daily: operational dashboards.",
                    "Monthly: scorecard review with the department head.",
                    "Quarterly: target reset and calibration.",
                ]),
                ("Data Sources", ["Curated BI models with data-as-of timestamps; no offline spreadsheets for official numbers."]),
                ("Policy code", [f"GEN-MET-{short.upper()}-2026-01 | Owner: Business Analytics CoE."]),
            ]),
        })

    tools = [
        ("News Feed", "news", "leadership notes, circulars and events"),
        ("Corporate Directory", "directory", "people and team contact details"),
        ("KM Portal", "km", "policies, process documents and FAQs"),
        ("Forms Portal", "forms", "downloadable and submittable forms"),
        ("Travel Desk", "travel", "domestic and international bookings"),
        ("Facilities Desk", "facilities", "seating, power and housekeeping"),
        ("LMS", "lms", "mandatory and role-based learning"),
        ("Feedback Portal", "feedback", "service ratings and pulse surveys"),
    ]
    for name, short, purpose in tools:
        docs.append({
            "bubble": "GENERAL", "slug": f"intranet_guide_{short}",
            "title": f"Intranet Guide: {name}",
            "body": _body([
                ("What It Is", [f"The {name} provides {purpose}."]),
                ("Getting There", ["Open the intranet home page and select the tile from the top navigation."]),
                ("Tips", [
                    "Use exact terms for search.",
                    "Check the publication date before relying on content.",
                ]),
                ("Support", ["Content queries route to Corporate Communications; access issues to the IT helpdesk."]),
                ("Policy code", [f"GEN-INT-{short.upper()}-2026-01 | Owner: Corporate Communications."]),
            ]),
        })

    glossaries = [
        ("Payments", "pay", ["UPI", "NEFT", "RTGS", "IMPS", "NACH", "ECS", "CTS", "BBPS"]),
        ("Credit", "credit", ["NPA", "LTV", "CIR", "EMI", "MCLR", "ECLGS", "CGTMSE", "SMA"]),
        ("Digital", "dig", ["API", "SSO", "OTP", "KYC", "VKYC", "A11Y", "UX", "SDK"]),
        ("HR", "hr", ["CTC", "LPA", "PIP", "IJP", "POSH", "UAN", "EPF", "VRS"]),
        ("Compliance", "comp", ["AML", "KYC", "PEP", "STR", "CTR", "FIU", "DPO", "RBI"]),
    ]
    for theme, short, terms in glossaries:
        lines = [f"- {t}: see the acronym dictionary for the full form and a plain-language note." for t in terms]
        docs.append({
            "bubble": "GENERAL", "slug": f"glossary_{short}",
            "title": f"Glossary: {theme}",
            "body": _body([
                ("Purpose", [f"Quick reference for common {theme} terms used in the bank."]),
                ("Terms", lines),
                ("Where To Go Deeper", [
                    "The full acronym dictionary and the role-based learning paths cover usage.",
                ]),
                ("Policy code", [f"GEN-GLOS-{short.upper()}-2026-01 | Owner: Learning & Development."]),
            ]),
        })

    # ------------------------------ CONVERSATIONAL_BI ------------------------------
    models = [
        ("Customer 360", "c360", "demographics, products and interactions"),
        ("CASA & Deposits", "casa", "balances, flows and deposit pricing"),
        ("Cards", "cards", "spends, payments, rewards and attrition"),
        ("Payments", "payments", "transaction success rates and failures"),
        ("Loans & Delinquency", "loans", "disbursals, buckets and collections"),
        ("Branch Performance", "branch", "acquisition, service and productivity"),
        ("Workforce", "wf", "headcount, attrition and learning metrics"),
    ]
    for name, short, scope in models:
        docs.append({
            "bubble": "CONVERSATIONAL_BI", "slug": f"model_notes_{short}",
            "title": f"Semantic Model Notes: {name}",
            "body": _body([
                ("Coverage", [f"This model covers {scope}."]),
                ("Grain", [
                    "Facts are at the transaction or event level; measures aggregate per the definitions.",
                ]),
                ("Key Dimensions", [
                    "Calendar, geography, channel and product, conformed across models.",
                ]),
                ("Caveats", [
                    "Late-arriving data updates are reflected at the next refresh.",
                    "Check the data-as-of timestamp before quoting numbers.",
                ]),
                ("Owner", ["Data Platform team with the business data owner."]),
                ("Policy code", [f"BI-MOD-{short.upper()}-2026-01 | Owner: Data Platform."]),
            ]),
        })

    metrics = [
        ("CASA Ratio", "casa", "deposit mix health"),
        ("Net Interest Margin", "nim", "core lending profitability"),
        ("Cost-to-Income", "cti", "operating efficiency"),
        ("Credit Cost", "ccost", "asset quality pressure"),
        ("Digital Adoption", "digadopt", "channel migration"),
        ("Net Promoter Score", "nps", "customer advocacy"),
        ("Active Rate", "active", "relationship engagement"),
    ]
    for name, short, why in metrics:
        docs.append({
            "bubble": "CONVERSATIONAL_BI", "slug": f"metric_dive_{short}",
            "title": f"Metric Deep-Dive: {name}",
            "body": _body([
                ("Why It Matters", [f"{name} indicates {why}."]),
                ("Definition", [
                    "See the KPI definition in the data dictionary; use the approved formula only.",
                ]),
                ("How To Read It", [
                    "Compare against the plan and the same period last year.",
                    "Break down by region, product or channel for drivers.",
                ]),
                ("Common Pitfalls", [
                    "Seasonality and one-off events can mislead; use rolling trends.",
                ]),
                ("Owner", ["The owning analytics team reviews changes quarterly."]),
                ("Policy code", [f"BI-KPI-{short.upper()}-2026-01 | Owner: Business Analytics CoE."]),
            ]),
        })

    use_cases = [
        ("Attrition Early Warning", "attrition", "flag at-risk employees using tenure, performance and engagement signals"),
        ("Spend Propensity", "propensity", "identify customers likely to adopt card or loan products"),
        ("Branch Productivity", "prod", "rank branches on acquisition per FTE and service quality"),
        ("Delinquency Segmentation", "deliq", "segment overdue accounts by risk for the right treatment"),
        ("Channel Migration", "migrate", "measure shift from branch to digital with cost impact"),
    ]
    for name, short, desc in use_cases:
        docs.append({
            "bubble": "CONVERSATIONAL_BI", "slug": f"usecase_{short}",
            "title": f"BI Use Case: {name}",
            "body": _body([
                ("Objective", [f"This use case aims to {desc}."]),
                ("Data Required", [
                    "Curated semantic models with row-level security per the access policy.",
                ]),
                ("Approach", [
                    "Define the target population and comparison window.",
                    "Validate findings against source dashboards before sharing.",
                ]),
                ("Outputs", [
                    "A dashboard or model scorecard with owners and a review cadence.",
                ]),
                ("Policy code", [f"BI-UC-{short.upper()}-2026-01 | Owner: Business Analytics CoE."]),
            ]),
        })

    # ------------------------------ AHA ------------------------------
    campaigns = [
        ("Referral Month", "referral", "boosted referral payouts and team leaderboards"),
        ("Service Excellence Sprint", "service", "CSAT-linked bonus points for frontline teams"),
        ("Certification Drive", "cert", "multiplier points for approved certification passes"),
        ("Cross-Sell League", "crosssell", "qualified cross-sell wins earn league points"),
        ("Digital Adoption Challenge", "digital", "branch and RM teams race on digital activation"),
    ]
    for name, short, desc in campaigns:
        docs.append({
            "bubble": "AHA", "slug": f"campaign_pack_{short}",
            "title": f"Campaign Pack: {name}",
            "body": _body([
                ("Campaign Idea", [desc + "."]),
                ("Eligibility", ["All eligible employees per the campaign brief; actions auto-track."]),
                ("Points", [
                    "Points and boosts follow the campaign matrix published on the portal.",
                ]),
                ("Timeline", [
                    "Campaign runs for the calendar quarter; payout within 30 days of close.",
                ]),
                ("Support", ["The campaign helpdesk responds within 3 business days."]),
                ("Policy code", [f"AHA-CP-{short.upper()}-2026-01 | Owner: Rewards & Recognition."]),
            ]),
        })

    awards = [
        ("Spot Award", "spot", "manager-issued recognition with a citation"),
        ("Team of the Quarter", "toq", "delivery narrative with business-head endorsement"),
        ("Collaboration Award", "collab", "cross-functional delivery with customer impact"),
        ("Customer Impact Award", "impact", "measurable customer outcome from a team"),
        ("Long-Service Award", "lsa", "milestone recognition at 5-year tiers"),
    ]
    for name, short, desc in awards:
        docs.append({
            "bubble": "AHA", "slug": f"nomination_{short}",
            "title": f"Nomination Guide: {name}",
            "body": _body([
                ("What It Recognises", [desc + "."]),
                ("How To Nominate", [
                    "1. Open the Aha portal > Awards > Nominate.",
                    "2. Complete the nomination form with a clear narrative.",
                    "3. Obtain the required endorsements.",
                ]),
                ("Evaluation", ["A cross-functional panel scores on impact and collaboration."]),
                ("Outcome", ["Winners receive points and recognition at the next town hall."]),
                ("Policy code", [f"AHA-NOM-{short.upper()}-2026-01 | Owner: Rewards & Recognition."]),
            ]),
        })

    cats = [
        ("E-Vouchers", "voucher", "retail, food, travel and wellness brands"),
        ("Electronics", "electronics", "audio, home and computing items"),
        ("Travel & Experiences", "travel", "curated events and getaways"),
        ("Wellness", "wellness", "fitness and health programmes"),
        ("Giving", "giving", "donate points to approved causes"),
    ]
    for name, short, desc in cats:
        docs.append({
            "bubble": "AHA", "slug": f"catalogue_{short}",
            "title": f"Points Catalogue: {name}",
            "body": _body([
                ("What's Inside", [f"{name} items cover {desc}."]),
                ("How It Works", [
                    "Browse the catalogue, add items to the cart and check out with points.",
                ]),
                ("Delivery", [
                    "E-vouchers deliver instantly; physical items ship in 7 to 10 business days.",
                ]),
                ("Changes", ["The catalogue refreshes quarterly; values are published in points."]),
                ("Policy code", [f"AHA-CAT-{short.upper()}-2026-01 | Owner: Rewards & Recognition."]),
            ]),
        })

    # ------------------------------ AXIS_PHONE ------------------------------
    queues = [
        ("Accounts", "accounts", "savings, current and deposit servicing"),
        ("Cards", "cards", "activation, disputes and limits"),
        ("Loans", "loans", "application status, EMI and foreclosure"),
        ("Wealth", "wealth", "priority and Burgundy servicing"),
        ("Complaints", "complaints", "grievance intake and follow-up"),
        ("Priority", "priority", "dedicated queue for priority customers"),
        ("Language Overflow", "lang", "regional-language support with translation backup"),
    ]
    for name, short, scope in queues:
        docs.append({
            "bubble": "AXIS_PHONE", "slug": f"queue_playbook_{short}",
            "title": f"Queue Playbook: {name}",
            "body": _body([
                ("Queue Scope", [f"The {name} queue handles {scope}."]),
                ("Handling Rules", [
                    "Verify identity before any account action.",
                    "Use the approved scripts for disclosures.",
                    "Dispose every call with a code and CRM summary.",
                ]),
                ("SLAs", [
                    "Priority: connect within 15 minutes of the slot.",
                    "Retail: connect within 60 minutes of the slot.",
                ]),
                ("Escalation", ["Escalate unresolved cases to the team lead same-day."]),
                ("Policy code", [f"AP-QP-{short.upper()}-2026-01 | Owner: Assisted Channels."]),
            ]),
        })

    scripts = [
        ("Welcome & Verification", "welcome", "greeting, identity checks and consent to record"),
        ("Complaint Intake", "intake", "acknowledgement, reference and resolution timeline"),
        ("Follow-Up", "followup", "status update and next action confirmation"),
        ("Apology & Recovery", "recovery", "acknowledge impact and offer the recovery option"),
        ("Upgrade Conversation", "upgrade", "need-based product conversation with disclosures"),
        ("Callback Confirmation", "cbconfirm", "confirm slot, topic and expected call window"),
    ]
    for name, short, scope in scripts:
        docs.append({
            "bubble": "AXIS_PHONE", "slug": f"script_pack_{short}",
            "title": f"Script Pack: {name}",
            "body": _body([
                ("When To Use", [f"Use this pack for {scope}."]),
                ("Key Elements", [
                    "1. Open with the standard greeting and the bank name.",
                    "2. Verify the customer per the authentication steps.",
                    "3. State the purpose and the required disclosures.",
                    "4. Confirm the outcome and the next action.",
                ]),
                ("Guardrails", [
                    "Scripts are mandatory for verifications and disclosures.",
                    "Do not improvise on terms, charges or timelines.",
                ]),
                ("Policy code", [f"AP-SC-{short.upper()}-2026-01 | Owner: Assisted Channels."]),
            ]),
        })

    features = [
        ("Callback Booking", "booking", "slot selection and confirmation"),
        ("Rescheduling", "resched", "slot changes before the callback"),
        ("Missed Callback Handling", "missed", "retry logic and follow-up"),
        ("Language Preference", "lang", "preference capture and routing"),
        ("Priority Callback", "priority", "dedicated slots and SLAs"),
        ("CSAT Survey", "csat", "post-call feedback loop"),
    ]
    for name, short, scope in features:
        docs.append({
            "bubble": "AXIS_PHONE", "slug": f"feature_guide_{short}",
            "title": f"Feature Guide: {name}",
            "body": _body([
                ("What It Does", [f"{name} covers {scope}."]),
                ("Customer View", [
                    "Customers manage the feature from the app, internet banking or the assistant.",
                ]),
                ("Agent View", [
                    "The agent console reflects the latest state and history.",
                ]),
                ("Edge Cases", [
                    "Escalate anomalies to the Assisted Channels support queue.",
                ]),
                ("Policy code", [f"AP-FG-{short.upper()}-2026-01 | Owner: Assisted Channels."]),
            ]),
        })

    # ------------------------------ DOWNLOAD ------------------------------
    packs = [
        ("HR Pack", "hr", "leave, reimbursement, statutory and separation forms"),
        ("Statutory Pack", "stat", "FEMA, KYC and FATCA/CRS forms"),
        ("IT Pack", "it", "service requests, access and security forms"),
        ("Customer Pack", "cust", "onboarding, accounts and grievance forms"),
        ("Compliance Pack", "comp", "declarations, registers and training acknowledgements"),
        ("Finance Pack", "fin", "vendor, payments and budget forms"),
    ]
    for name, short, contents in packs:
        docs.append({
            "bubble": "DOWNLOAD", "slug": f"pack_index_{short}",
            "title": f"{name} Index",
            "body": _body([
                ("Contents", [f"The {name} contains {contents}."]),
                ("How To Use", [
                    "Search by form name or code on the Download portal.",
                    "Only the latest version is valid for submission.",
                ]),
                ("Owners", [
                    "Each form lists its owner; content queries go to the owner.",
                ]),
                ("Policy code", [f"DL-PK-{short.upper()}-2026-01 | Owner: Corporate Communications."]),
            ]),
        })

    walkthroughs = [
        ("HR-LEAVE-01", "leave", "special leave application", "HR"),
        ("HR-TRVL-01", "trvl", "travel expense statement", "HR"),
        ("IT-SW-01", "sw", "new software request", "IT"),
        ("KYC-INDV-01", "kyc", "individual KYC application", "Compliance"),
        ("FIN-VEND-01", "vend", "new vendor setup", "Finance"),
        ("GRV-01", "grv", "customer grievance form", "Customer Advocacy"),
        ("NOM-01", "nom", "nomination for deposit accounts", "Branch Ops"),
    ]
    for form, short, purpose, owner in walkthroughs:
        docs.append({
            "bubble": "DOWNLOAD", "slug": f"walkthrough_{short}",
            "title": f"Form Walkthrough: {form}",
            "body": _body([
                ("Purpose", [f"{form} is the {purpose} form."]),
                ("Filling It Out", [
                    "1. Download the latest version from the portal.",
                    "2. Complete every mandatory field; avoid abbreviations.",
                    "3. Attach supporting documents in accepted formats.",
                ]),
                ("Submission", [f"Submit per the form instructions; the owning team is {owner}."]),
                ("After Submission", ["Track the reference in the owning system; SLA per the service standards."]),
                ("Policy code", [f"DL-FW-{short.upper()}-2026-01 | Owner: {owner}."]),
            ]),
        })

    subm_guides = [
        ("Leave Application", "leave", "HR portal or the branch HR coordinator"),
        ("Travel Claim", "travel", "HR portal with receipts"),
        ("Software Request", "sw", "Unidesk with justification"),
        ("KYC Update", "kyc", "branch with the checklist"),
        ("Vendor Setup", "vendor", "finance portal with GST and bank details"),
        ("Grievance Submission", "grv", "grievance portal with the reference"),
    ]
    for name, short, route in subm_guides:
        docs.append({
            "bubble": "DOWNLOAD", "slug": f"submission_{short}",
            "title": f"Submission Guide: {name}",
            "body": _body([
                ("Where To Submit", [f"Submit the {name} through the {route}."]),
                ("Preparation", [
                    "Keep the form code and supporting documents ready.",
                    "Check the latest form version before filling.",
                ]),
                ("Common Issues", [
                    "Rejected submissions state the reason; correct and resubmit.",
                ]),
                ("Tracking", ["Use the submission reference to track status."]),
                ("Policy code", [f"DL-SUB-{short.upper()}-2026-01 | Owner: Corporate Communications."]),
            ]),
        })

    return docs


# ---------------------------------------------------------------------------

def main() -> None:
    _write_faqs()
    _clean_generated()
    _emit_docs(_build_docs())


if __name__ == "__main__":
    main()
