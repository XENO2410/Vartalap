"""LAW + FINANCIAL_ADVISOR + CR corpora.

Facts grounded in widely known Indian statutory/regulatory frameworks (PMLA,
DPDP Act, RBI KYC directions, SEBI/IRDAI norms, IT Act, Sarfaesi, FEMA etc.);
all bank-specific figures, codes and owners are synthetic. Original prose.
"""

DOCS = [
# ================================================================ LAW
{
 "bubble": "LAW",
 "slug": "whistleblower_policy",
 "title": "Whistleblower Policy",
 "body": """
## Purpose
The policy enables employees and third parties to report suspected misconduct,
fraud, regulatory violations or ethical breaches without fear of retaliation.

## Channels
Reports may be submitted through the dedicated whistleblower portal, email or
postal address managed by the ethics committee. Anonymous reporting is permitted.

## Confidentiality
The identity of the whistleblower is protected to the extent permitted by law.
Breach of confidentiality by investigation teams is a disciplinary offence.

## Protection
Good-faith reports do not attract adverse consequences. Vexatious or malicious
complaints are themselves subject to disciplinary action.

## Investigation
The ethics committee triages and investigates reports, engaging Internal Audit,
Compliance or external experts as needed. Outcomes are reported to the Audit
Committee of the Board.

Policy code: LAW-WB-2026-01 | Owner: Ethics & Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "anti_bribery_corruption",
 "title": "Anti-Bribery & Corruption Policy",
 "body": """
## Applicability
The policy applies to all employees, agents, vendors and intermediaries acting
for the bank, aligned with the Prevention of Corruption Act, 1988 and
international anti-bribery conventions.

## Prohibited Conduct
- Offering, promising or giving anything of value to influence a public official.
- Facilitation payments of any size.
- Commercial bribery between private parties.

## Due Diligence
Third parties are screened before engagement and re-screened periodically.
High-risk intermediaries require enhanced due diligence.

## Record-Keeping
Hospitality, gifts and donations are recorded with adequate particulars. Accounts
must not be falsified to conceal any payment.

## Reporting
Suspected bribery is reported through the whistleblower channel. Non-compliance
may result in termination and regulatory reporting.

Policy code: LAW-ABC-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "insider_trading_policy",
 "title": "Insider Trading Policy",
 "body": """
## Regulatory Basis
The policy implements the SEBI (Prohibition of Insider Trading) Regulations,
2015 for employees with access to unpublished price-sensitive information (UPSI).

## UPSI
UPSI includes unpublished financial results, capital actions, mergers,
acquisitions and major business developments.

## Trading Windows
Trading in the bank's securities is permitted only during open windows announced
by the compliance team. Closed windows apply around results and major events.

## Pre-Clearance
Designated persons require pre-clearance for trades above the threshold and must
hold positions for the prescribed minimum period.

## Disclosures
Designated persons file initial and continuous disclosures of holdings and trades
as required by the regulations.

Policy code: LAW-INSIDER-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "data_breach_response",
 "title": "Data Breach Response Protocol",
 "body": """
## Detection
Security events are detected through monitoring tools, staff reports and vendor
alerts. Every suspected personal-data breach is logged as a Priority-Zero incident.

## Containment
Containment includes isolating affected systems, revoking compromised credentials
and preserving forensic evidence without modification.

## Notification
Notifiable breaches are reported to the Data Protection Board within 72 hours
under the DPDP framework, and affected data principals are informed promptly.

## Investigation
Root-cause analysis is completed within 15 working days. Corrective actions are
tracked to closure with the Chief Information Security Officer.

## Review
The breach register is reviewed quarterly by the Risk Management Committee.

Policy code: LAW-BR-2026-01 | Owner: Data Protection Office.
"""
},
{
 "bubble": "LAW",
 "slug": "dpdp_consent_management",
 "title": "Consent Management under DPDP",
 "body": """
## Consent Principles
Consent for processing personal data must be free, specific, informed,
unconditional and unambiguous, with clear affirmative action.

## Notice Requirements
Every consent request describes the personal data collected, purpose, rights of
the data principal and grievance mechanism in clear, plain language.

## Withdrawal
Data principals may withdraw consent as easily as it was given. Processing stops
after withdrawal, subject to statutory retention obligations.

## Record-Keeping
Consent records with timestamps and versions are retained as evidence of lawful
processing.

## Children's Data
Verifiable parental consent is mandatory for processing data of individuals below
18 years of age.

Policy code: LAW-DPDP-C-2026-01 | Owner: Data Protection Office.
"""
},
{
 "bubble": "LAW",
 "slug": "rbi_kyc_master_direction",
 "title": "KYC Master Direction Essentials",
 "body": """
## Regulatory Basis
Customer onboarding follows the RBI Master Direction on Know Your Customer,
2016 (as amended).

## CDD at Onboarding
- Identify and verify the customer using Officially Valid Documents.
- Verify beneficial owners for non-individual customers.
- Assign a risk category: low, medium or high.

## Periodic Updation
High-risk customers: KYC refreshed every 2 years. Medium: every 8 years.
Low: every 10 years. Re-KYC is event-driven for significant changes.

## Enhanced Due Diligence
EDD applies to PEPs, high-risk geographies and high-value or complex
transactions, including source-of-funds checks.

## Record Retention
KYC records are maintained for the prescribed period after account closure as
per PMLA requirements.

Policy code: LAW-KYC-RBI-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "pmla_obligations",
 "title": "PMLA Obligations Overview",
 "body": """
## Regulatory Basis
The Prevention of Money Laundering Act, 2002 obligates the bank to detect,
deter and report money-laundering activity.

## Reporting Officers
The Principal Officer is responsible for filings with FIU-IND. Every business
unit designates a compliance liaison.

## Transaction Monitoring
Automated and rule-based monitoring flags unusual patterns: structuring,
rapid movement, high-risk jurisdiction flows and unexpected activity.

## Reporting Obligations
Cash Transaction Reports, Suspicious Transaction Reports, Counterfeit Currency
Reports and Cross-Border Wire Transfer Reports are filed within statutory
timelines.

## Training
All customer-facing staff complete annual AML training; completion is tracked
and audited.

Policy code: LAW-PMLA-2026-01 | Owner: Financial Crime Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "fiu_reporting_guide",
 "title": "FIU-IND Reporting Guide",
 "body": """
## Report Types
- CTR: cash transactions above the threshold per customer per day.
- STR: suspicious transactions, filed within the statutory timeline after detection.
- CCR: counterfeit currency incidents.
- CBWTR: cross-border wire transfers above the threshold.

## Quality Standards
Reports include complete identifiers, transaction details, account references
and a clear description of suspicion for STRs.

## Confidentiality
Reporting activity is confidential. Customers must not be tipped off about an
STR under any circumstance.

## Post-Reporting
The bank preserves underlying records and responds to FIU-IND requisitions
within prescribed timelines.

Policy code: LAW-FIU-2026-01 | Owner: Financial Crime Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "fraud_monitoring_policy",
 "title": "Fraud Monitoring Policy",
 "body": """
## Scope
Covers internal fraud, external fraud against customers, and cyber-fraud across
channels.

## Early Warning Signals
Behavioural, transactional and system-level red flags are defined per channel
and reviewed for tuning quarterly.

## Investigation
Suspect cases are investigated by the fraud risk management unit with
preservation of evidence and defined escalation timelines.

## Reporting
Frauds above thresholds are reported to the RBI within prescribed timelines and
to law enforcement where required.

## Prevention
Root-cause learnings feed policy changes, staff training and control
enhancements tracked to closure.

Policy code: LAW-FRAUD-2026-01 | Owner: Fraud Risk Management.
"""
},
{
 "bubble": "LAW",
 "slug": "third_party_risk_policy",
 "title": "Third-Party Risk Management",
 "body": """
## Scope
Applies to vendors, service providers, fintech partners and outsourcing
arrangements with access to bank data, systems or customers.

## Onboarding Diligence
Financial, operational, reputational, data-security and regulatory screening
before contract signing. High-risk categories require enhanced checks.

## Contractual Controls
Contracts include data-protection clauses, audit rights, business continuity
obligations and incident notification timelines.

## Ongoing Monitoring
Periodic re-assessment, SLA reviews and security posture checks. Critical
vendors are re-assessed at least annually.

## Exit
Off-boarding includes data return/destruction certification and access
revocation verification.

Policy code: LAW-TPRM-2026-01 | Owner: Vendor Risk Office.
"""
},
{
 "bubble": "LAW",
 "slug": "vendor_due_diligence",
 "title": "Vendor Due Diligence Standard",
 "body": """
## Core Checks
- Incorporation and existence verification.
- Ultimate beneficial ownership identification.
- Sanctions, negative news and litigation screening.
- Financial health assessment.

## Risk Tiers
Vendors are tiered by spend, data access and criticality. Tier-1 vendors face
the full due-diligence scope.

## Documentation
Due-diligence packs are retained for audit and refreshed annually or on
material change.

## Failure Handling
Failed due diligence leads to engagement rejection or termination with
business continuity support.

Policy code: LAW-VDD-2026-01 | Owner: Vendor Risk Office.
"""
},
{
 "bubble": "LAW",
 "slug": "outsourcing_guidelines",
 "title": "Outsourcing Governance Guidelines",
 "body": """
## Regulatory Basis
Outsourcing of material activities follows RBI guidelines on outsourcing of
financial services.

## Materiality Assessment
Activities are assessed for materiality based on impact on customers, data
confidentiality, regulatory reporting and business continuity.

## Board Oversight
Material outsourcing arrangements are approved by the board or its committee.
The outsourcing policy is reviewed annually.

## Service Provider Management
SLAs, audit rights, sub-contracting restrictions and exit clauses are mandated
in contracts.

## Records
The register of outsourcing arrangements is maintained centrally and available
to auditors and supervisors.

Policy code: LAW-OS-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "banking_ombudsman_process",
 "title": "Banking Ombudsman Process",
 "body": """
## Overview
The Banking Ombudsman Scheme provides a free grievance mechanism for customers
whose complaints remain unresolved by the bank.

## Escalation Path
1. Customer raises a complaint with the bank's internal grievance cell.
2. If unresolved or rejected within 30 days, the customer may approach the
   Ombudsman for the region.
3. Ombudsman may mediate or pass an award within prescribed limits.

## Bank Obligations
The bank appoints a nodal officer, files required returns, and implements awards
within prescribed timelines.

## Appeal
Either party may appeal the Ombudsman's award to the appellate authority.

Policy code: LAW-OB-2026-01 | Owner: Customer Advocacy.
"""
},
{
 "bubble": "LAW",
 "slug": "customer_grievance_redressal",
 "title": "Customer Grievance Redressal Policy",
 "body": """
## Channels
Customers may raise complaints through branches, contact centre, internet
banking, mobile app or the dedicated grievance portal.

## Acknowledgement
Every complaint receives an acknowledgement with a reference number immediately
on registration.

## Turnaround
Standard complaints: 7 working days. Complex complaints involving investigation:
30 days. Exceptions are communicated with reasons.

## Escalation
Unresolved complaints escalate to the nodal officer, then the Principal Nodal
Officer, then the Ombudsman.

## Root-Cause Review
Repeated complaint categories are reviewed monthly to fix underlying causes.

Policy code: LAW-CGR-2026-01 | Owner: Customer Advocacy.
"""
},
{
 "bubble": "LAW",
 "slug": "it_act_obligations",
 "title": "Information Technology Act Obligations",
 "body": """
## Regulatory Basis
The Information Technology Act, 2000 (as amended) governs electronic records,
cyber-security obligations and intermediary responsibilities.

## Electronic Records
The bank maintains legally valid electronic records with audit trails for
transactions, authentication events and disclosures.

## Cyber-Security Directions
The bank follows RBI cyber-security directions including incident reporting
timelines, security operations and board-level oversight.

## Incident Reporting
Cyber incidents are reported to CERT-In within prescribed timelines, with
preservation of logs and evidence.

## Awareness
Annual cyber-awareness training is mandatory for all employees.

Policy code: LAW-ITACT-2026-01 | Owner: Information Security.
"""
},
{
 "bubble": "LAW",
 "slug": "cybersecurity_framework",
 "title": "Cyber-Security Framework",
 "body": """
## Governance
Cyber-security is governed by the board-level Information Security Committee
with quarterly reviews of posture, incidents and audit findings.

## Controls Domains
- Identity and access management, including MFA for privileged access.
- Network segmentation and perimeter defence.
- Vulnerability management with defined remediation SLAs.
- Security monitoring and incident response.

## Assurance
Annual VAPT, red-team exercises for critical assets, and external audits per
RBI guidelines.

## Incident Response
The incident response plan defines roles, escalation, evidence preservation and
regulatory reporting timelines.

Policy code: LAW-CYBER-2026-01 | Owner: Information Security.
"""
},
{
 "bubble": "LAW",
 "slug": "payment_systems_regulation",
 "title": "Payment Systems Overview",
 "body": """
## Regulatory Basis
Payment operations follow the Payment and Settlement Systems Act, 2007 and
RBI directions on digital payments.

## Authorisation
The bank operates approved payment systems — UPI, NEFT, RTGS, cards and wallets
— under board-approved policies.

## Customer Protection
Limits, cooling periods and dispute timelines follow RBI circulars. Unauthorised
transaction liability follows the zero/limited-liability framework.

## Operational Resilience
Payment systems maintain defined availability targets, fallback arrangements
and regular recovery drills.

## Reporting
Periodic returns and incident notifications are filed with the RBI within
prescribed timelines.

Policy code: LAW-PSS-2026-01 | Owner: Payments Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "negotiable_instruments_act",
 "title": "Negotiable Instruments Essentials",
 "body": """
## Scope
The Negotiable Instruments Act, 1881 governs cheques, promissory notes and
bills of exchange.

## Cheque Dishonour
Dishonoured cheques attract penalties and may lead to proceedings under
Section 138 upon statutory notice and non-payment within 15 days.

## Endorsement
Instruments are negotiated by endorsement and delivery. The bank verifies
endorsements per prescribed procedures.

## Paying Bank Duties
Payment in due course protects the bank. Alterations material to the instrument
render it invalid unless authenticated.

## Training
Ops staff complete annual NI Act refreshers on dishonour handling and returns.

Policy code: LAW-NI-2026-01 | Owner: Operations Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "sarfaesi_overview",
 "title": "SARFAESI Overview for Staff",
 "body": """
## Regulatory Basis
The Securitisation and Reconstruction of Financial Assets and Enforcement of
Security Interest Act, 2002 enables secured creditors to enforce security
interests without court intervention.

## Key Stages
- Classification of the account as NPA.
- Demand notice under Section 13(2) with a 60-day period.
- Possession, sale or transfer of secured assets if dues remain unpaid.

## Borrower Remedies
Borrowers may object to the notice, seek account review, and approach the
Debts Recovery Tribunal within prescribed timelines.

## Staff Conduct
Only trained recovery staff handle SARFAESI actions. Fair-practices codes for
recovery agents are strictly followed.

Policy code: LAW-SARFAESI-2026-01 | Owner: Legal.
"""
},
{
 "bubble": "LAW",
 "slug": "deposit_insurance",
 "title": "Deposit Insurance Coverage",
 "body": """
## Scheme
Deposits are insured by the Deposit Insurance and Credit Guarantee Corporation
(DICGC) up to the prescribed ceiling per depositor per bank.

## Coverage
Savings, current, fixed and recurring deposits in a bank are covered. Coverage
extends to the aggregate of a depositor's accounts with the same bank.

## Exclusions
Inter-bank deposits, government deposits and deposits of foreign governments
are excluded.

## Claim Process
In a liquidation scenario, DICGC settles claims up to the insured amount within
prescribed timelines.

## Customer Communication
Branches display DICGC coverage information and respond to customer queries on
the scheme.

Policy code: LAW-DICGC-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "fema_overview",
 "title": "FEMA Essentials for Branches",
 "body": """
## Regulatory Basis
The Foreign Exchange Management Act, 1999 governs cross-border transactions,
current and capital account dealings.

## Current Account
Current account transactions are generally permitted subject to scheduled
restrictions. Authorised dealer branches process remittances within limits.

## Capital Account
Capital account transactions require RBI approval or are governed by
specific schedules (FDI, ODI, borrowings).

## Reporting
Authorised dealers report transactions through the prescribed RBI returns and
the FIRMS/FETERS systems within timelines.

## Penalties
Contraventions attract penalties up to prescribed multiples of the amount
involved and may include compounding.

Policy code: LAW-FEMA-2026-01 | Owner: Treasury Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "consumer_protection_act",
 "title": "Consumer Protection Act Basics",
 "body": """
## Applicability
The Consumer Protection Act, 2019 protects consumers against unfair trade
practices and deficient services.

## Key Concepts
- Deficiency in service: fault, imperfection or inadequacy in the quality of
  service.
- Unfair contract: terms causing significant change in consumer rights.
- Product liability: manufacturer and service-provider liability for harm.

## Redressal Forums
District, State and National Commissions adjudicate complaints by value of
claim. E-filing is available.

## Bank Practices
The bank maintains transparent terms, plain-language documents and fair
grievance mechanisms to minimise disputes.

Policy code: LAW-CPA-2026-01 | Owner: Legal.
"""
},
{
 "bubble": "LAW",
 "slug": "document_retention_policy",
 "title": "Document Retention Policy",
 "body": """
## Principles
Records are retained for legal, regulatory, tax and business needs and disposed
of thereafter through an approved process.

## Retention Classes
- KYC and transaction records: as per PMLA requirements.
- Tax records: as per Income-Tax Act.
- Employment records: as per labour statutes.
- Contracts: for the contract term plus limitation periods.

## Litigation Hold
When litigation or investigation is anticipated, relevant records are preserved
notwithstanding retention expiry.

## Disposal
Disposal uses shredding or certified digital erasure with an audit trail.

Policy code: LAW-RET-2026-01 | Owner: Records Management.
"""
},
{
 "bubble": "LAW",
 "slug": "e_signature_guidelines",
 "title": "Electronic Signature Guidelines",
 "body": """
## Legal Basis
Electronic signatures are governed by the Information Technology Act, 2000
read with contractual and internal delegation authorities.

## Acceptable Forms
Digital signatures with valid DSC certificates and Aadhaar e-sign where
permitted are acceptable for internal and customer documents.

## Execution Authority
The delegation-of-authority matrix defines who may e-sign which document
class. Signatures outside authority are void.

## Records
Executed documents are stored with signature metadata, timestamp and audit
trail in the document management system.

Policy code: LAW-ESIGN-2026-01 | Owner: Legal.
"""
},
{
 "bubble": "LAW",
 "slug": "legal_hold_process",
 "title": "Legal Hold Process",
 "body": """
## Trigger Events
Litigation notice, regulatory enquiry, audit requirement or anticipated
dispute triggers a legal hold.

## Hold Notice
Legal issues a hold notice identifying custodians, systems and records in
scope. Custodians must preserve all relevant data.

## Scope
Email, documents, chat, databases and paper records related to the matter.

## Release
On matter closure, Legal issues a release notice and normal retention resumes.

## Non-Compliance
Failure to preserve under a hold is escalated as a compliance breach.

Policy code: LAW-HOLD-2026-01 | Owner: Legal.
"""
},
{
 "bubble": "LAW",
 "slug": "subpoena_and_notice_handling",
 "title": "Subpoena & Regulatory Notice Handling",
 "body": """
## Receipt
All court summons, subpoenas, and regulatory requisitions route through the
central legal intake inbox within 24 hours of receipt.

## Response Ownership
Legal coordinates with business, compliance and operations to compile
responses. Internal deadlines are set at least three days before external
deadlines.

## Confidentiality
Only authorised personnel handle the matter. Responding parties are restricted
to named custodians.

## Record-Keeping
A register records the notice, response timeline, produced documents and
closure.

Policy code: LAW-SUBP-2026-01 | Owner: Legal.
"""
},
{
 "bubble": "LAW",
 "slug": "market_conduct_standards",
 "title": "Market Conduct Standards",
 "body": """
## Fair Dealing
Products and communications must be fair, transparent and non-misleading.
Employees must not make promises outside approved product features.

## Suitability
Sales follow the suitability framework: risk profiling, need analysis and
appropriate product mapping with documented consent.

## Grievance Readiness
Customers receive clear pre-contractual disclosures including terms, charges
and grievance channels.

## Mis-selling
Mis-selling attracts disciplinary action and may be reported to regulators.

Policy code: LAW-MC-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "LAW",
 "slug": "recorded_calls_compliance",
 "title": "Call Recording & Monitoring Standards",
 "body": """
## Purpose
Calls in sales and service channels are recorded for quality, dispute
resolution and regulatory compliance.

## Disclosure
Customers are informed of recording through IVR announcements and in
channel terms.

## Storage
Recordings are encrypted, retained per the retention schedule and accessible
only to authorised roles.

## Usage
Recordings may be used for quality monitoring, training, investigation and
regulatory response. They are never shared outside authorised processes.

Policy code: LAW-CALLREC-2026-01 | Owner: Compliance.
"""
},
# ================================================== FINANCIAL_ADVISOR
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "savings_account_products",
 "title": "Savings Account Products",
 "body": """
## Product Range
- Basic savings: zero-balance variant per RBI guidelines.
- Regular savings with tiered interest.
- Salary accounts with bundled benefits.
- Premium savings with lifestyle and banking privileges.

## Eligibility
Resident individuals, HUFs in select variants, and minors through guardians.
NRI variants are offered under NRE/NRO schemes.

## Interest
Interest is credited quarterly based on daily balances, as per prevailing
rates published on the website.

## Value-Adds
Debit cards, digital banking, sweep facilities and insurance covers vary by
variant and are detailed in the product one-pager.

Advisory note: confirm the latest features from the product master before
quoting to customers.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "current_account_products",
 "title": "Current Account Products",
 "body": """
## Segments
Current accounts serve proprietorships, partnerships, companies, trusts and
societies.

## Variants
- Basic current for small businesses.
- Business current with bundled digital tools.
- Premium current for mid-corporates with dedicated RM support.

## Features
High transaction limits, cash management services, bulk payments, and
overdraft linkage subject to approval.

## Documentation
Business registration proof, KYC of all authorised signatories, board
resolution for companies, and trust deed for trusts.

Advisory note: quote transaction charges from the tariff schedule.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "credit_card_variants",
 "title": "Credit Card Variants",
 "body": """
## Portfolio
- Entry cards for first-time users.
- Rewards cards with accelerated points on categories.
- Cashback cards for everyday spends.
- Travel and premium cards with lounge and milestone benefits.

## Eligibility
Age 21-65 (primary), income thresholds by variant, good bureau score and
internal policy checks.

## Features
Interest-free period up to the prescribed days, EMI conversion, balance
transfer (subject to policy) and fraud cover.

## Billing
Billing cycle and due dates are defined at issuance. Minimum amount due and
late-payment implications are in the cardholder agreement.

Advisory note: always disclose fees, charges and interest to customers
before recommending a card.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "personal_loans",
 "title": "Personal Loans",
 "body": """
## Product
Unsecured term loan for salaried and self-employed customers.

## Quantum and Tenure
Loan amounts up to the approved multiple of income, tenure up to the
prescribed years, subject to policy.

## Eligibility
Stable income, employer category, bureau score and debt-to-income ratio
within policy thresholds.

## Charges
Processing fee, prepayment charges (post lock-in) and penal interest as per
the published tariff.

## Disbursement
Disbursement follows documentation completion, credit approval and
agreement execution.

Advisory note: recommend based on repayment capacity, not just eligibility.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "home_loan_products",
 "title": "Home Loan Products",
 "body": """
## Product Range
- Purchase of new/resale property.
- Construction and plot loans.
- Home improvement and balance transfer.
- Top-up loans for existing borrowers.

## Key Parameters
Loan-to-value up to the prescribed RBI-permitted ratio, tenure up to the
prescribed years, and rate linkage to the benchmark as chosen.

## Documentation
Property documents with legal and technical evaluation, income proof and
KYC of all applicants.

## Tax Benefit
Principal under Section 80C and interest under Section 24(b) within
statutory limits — customers should consult tax advisors.

Advisory note: highlight insurance options and foreclosure terms.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "car_loans",
 "title": "Car Loans",
 "body": """
## Product
Financing for new and pre-owned cars, including electric vehicles with
scheme-specific rates.

## Quantum and Tenure
Up to the prescribed percentage of on-road price for new cars, lower for
pre-owned. Tenure up to the prescribed years.

## Eligibility
Age, income stability and bureau profile within policy thresholds. Co-applicant
income may be combined.

## Charges
Processing fee, foreclosure charges post lock-in and documentation charges
per tariff.

## Process
Sanction based on income and bureau check, disbursement to dealer or
seller after hypothecation documentation.

Advisory note: compare on-road price funding vs ex-showroom funding for the
customer.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "education_loans",
 "title": "Education Loans",
 "body": """
## Purpose
Financing for recognised courses in India and abroad — tuition, hostel,
exams and related costs.

## Quantum
Up to the prescribed amount for domestic and higher amounts for select
institutions abroad, with collateral requirements as per policy.

## Moratorium
Course duration plus a prescribed grace period, during which simple
interest applies per scheme.

## Eligibility
Admission to a recognised institution, co-applicant (parent/guardian) and
collateral as applicable.

## Disbursement
Stage-wise directly to the institution or against fee receipts.

Advisory note: inform customers about interest subsidy schemes where
eligible.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "gold_loans",
 "title": "Gold Loans",
 "body": """
## Product
Secured loan against gold ornaments, with quick turnaround.

## Quantum
Loan-to-value as per RBI-prescribed limits on the pledged gold value.

## Process
Gold appraisal at the branch by certified valuators, agreement execution
and immediate disbursement.

## Tenure and Repayment
Tenure up to the prescribed months with bullet or EMI repayment options.

## Security
Gold is stored in dual-custody vaults and insured. Non-payment leads to
auction after due process per policy.

Advisory note: always explain auction terms and interest structure clearly.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "ppf_scheme",
 "title": "Public Provident Fund (PPF)",
 "body": """
## Features
- 15-year tenure, extendable in 5-year blocks.
- Deposit range from the statutory minimum to maximum per financial year.
- Interest compounded annually at government-notified rates.

## Tax Benefits
Deposits qualify under Section 80C; interest and maturity are exempt,
subject to prevailing rules.

## Withdrawals and Loans
Partial withdrawals from the 7th year and loans from the 3rd year subject
to scheme rules.

## Premature Closure
Allowed only for specified life events (medical, education) per scheme
conditions.

Advisory note: PPF suits long-horizon tax-efficient accumulation.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "nps_guide",
 "title": "National Pension System (NPS) Guide",
 "body": """
## Structure
NPS is a defined-contribution retirement scheme regulated by PFRDA with
tier-I (retirement) and tier-II (voluntary) accounts.

## Asset Classes
Equity, corporate bonds, government securities and alternate assets with
allocation caps per PFRDA rules. Active and auto choice available.

## Tax Benefits
Contributions under 80CCD(1)/(1B) within limits; employer contributions
under 80CCD(2).

## Exit Rules
On maturity, up to the prescribed percentage may be withdrawn lump-sum
with the balance annuitised.

## Suitability
NPS suits investors seeking market-linked, low-cost retirement
accumulation with annuitisation at maturity.

Advisory note: explain lock-in and annuity purchase requirement.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "sukanya_samriddhi",
 "title": "Sukanya Samriddhi Account",
 "body": """
## Purpose
Small-savings scheme for the girl child, opened before age 10 and operated
until she turns 21.

## Deposits
Minimum annual deposit as prescribed, maximum per year. Interest is
government-notified, compounded annually.

## Tax Benefits
Deposits under Section 80C; interest and maturity exempt under the scheme.

## Withdrawal Rules
Partial withdrawal (up to the prescribed percentage) for higher education
after age 18; maturity at 21 years or on marriage after 18.

## Operation
Operated by the guardian until majority, then by the account holder.

Advisory note: emphasise the lock-in before recommending.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "senior_citizen_savings",
 "title": "Senior Citizen Savings Scheme",
 "body": """
## Eligibility
Individuals aged 60 and above; 55-60 for those who retired under
superannuation/VRS within the prescribed rules.

## Features
- Tenure of 5 years, extendable once by 3 years.
- Quarterly interest at government-notified rates.
- Deposit limits per scheme rules; joint accounts with spouse allowed.

## Tax
Deposits qualify under Section 80C. Interest is taxable and subject to TDS.

## Premature Closure
Allowed with penalty after the first year except death cases.

Advisory note: compare SCSS with the Senior Citizens Savings and monthly
income options.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "term_insurance_products",
 "title": "Term Insurance Products",
 "body": """
## Product
Pure protection life cover for a chosen term and sum assured.

## Variants
- Level term: fixed cover throughout.
- Increasing cover: grows with inflation-linked steps.
- Return of premium: refund of premiums on survival (higher premium).

## Key Features
High cover at low premium, riders for critical illness and accidental death,
and tax benefits under 80C and 10(10D).

## Underwriting
Medical underwriting based on age, health disclosures and habits.

Advisory note: recommend cover of 10-15x annual income as a starting rule.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "ulip_overview",
 "title": "Unit-Linked Insurance Plans (ULIP)",
 "body": """
## Structure
ULIPs combine insurance cover with market-linked investment in equity,
debt or balanced funds.

## Key Parameters
- 5-year lock-in period.
- Fund switches allowed; charges include premium allocation, policy
  administration, fund management and mortality.

## Tax
Premiums under 80C (subject to conditions); maturity proceeds under
10(10D) subject to premium limits.

## Suitability
Long-horizon investors comfortable with market risk who want insurance
and investment in one product.

Advisory note: disclose all charges and compare with term-plus-MF
alternatives.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "general_insurance_products",
 "title": "General Insurance Products",
 "body": """
## Lines Offered
- Motor: comprehensive and third-party.
- Health: individual, family floater and top-up.
- Home: structure and contents.
- Travel: international and domestic.

## Bancassurance
Products are sold through the bank's approved insurer partners under the
corporate agency arrangement.

## Claims
Claims follow the insurer's process; the bank assists with documentation
and status follow-up.

## Code of Conduct
Advisors must hold required certifications and follow IRDAI advertisement
and disclosure norms.

Advisory note: always explain exclusions and waiting periods in health.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "wealth_management_tiers",
 "title": "Wealth Management Tiers",
 "body": """
## Tiering
- Classic: entry wealth tier with branch-based service.
- Priority: dedicated RM and priority banking services.
- Burgundy/Private: bespoke advisory, family office support for UHNI.

## Services
Portfolio reviews, estate planning referrals, tax planning guidance and
preferential pricing.

## Suitability
Tiering is based on relationship value; products remain subject to
suitability and risk profiling.

## Governance
Advisory conversations are recorded and reviewed for mis-selling controls.

Advisory note: tier upgrades are based on total relationship value.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "burgundy_private_banking",
 "title": "Burgundy Private Banking",
 "body": """
## Offering
Dedicated relationship coverage for UHNI clients: investment advisory,
credit solutions, structured products (where eligible) and succession
planning referrals.

## Eligibility
Entry thresholds are defined by investible assets or relationship value
per the published criteria.

## Services
- Multi-asset portfolio construction.
- Bespoke credit and banking solutions.
- Access to alternates and pre-IPO opportunities subject to eligibility.

## Governance
All recommendations follow suitability and distribution policies with
documented risk profiling.

Advisory note: private banking referrals require relationship-banking
approvals.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "portfolio_review_process",
 "title": "Portfolio Review Process",
 "body": """
## Cadence
Portfolio reviews occur at least annually, and semi-annually for Priority
and Burgundy relationships.

## Steps
1. Reconfirm goals and risk profile.
2. Review asset allocation against the model portfolio.
3. Identify drift, underperformers and rebalancing needs.
4. Document recommendations and client decisions.

## Records
Review notes, suitability reports and consent records are stored in the
advisory system.

## Governance
Reviews are sampled by quality assurance for suitability compliance.

Advisory note: rebalance only with client consent and transaction-cost
awareness.
"""
},
{
 "bubble": "FINANCIAL_ADVISOR",
 "slug": "risk_profiling_framework",
 "title": "Risk Profiling Framework",
 "body": """
## Components
Risk profiling combines:
- Risk capacity: income, assets, liabilities, horizon.
- Risk tolerance: questionnaire-based willingness to bear loss.
- Experience: investment literacy and history.

## Bands
Conservative, Moderate and Aggressive bands map to model allocations.

## Re-Profiling
Re-profile on material life changes or at least every two years.

## Suitability Rule
Products outside the risk band need written client acknowledgment.

Advisory note: never skip profiling for transaction convenience.
"""
},
# ================================================================ CR
{
 "bubble": "CR",
 "slug": "cr_lifecycle",
 "title": "Change Request Lifecycle",
 "body": """
## Stages
1. Draft: business case and impact assessment.
2. Review: technical and risk review with peer checks.
3. Approval: CAB or emergency CAB as applicable.
4. Implementation: within the approved window.
5. Post-implementation review and closure.

## State Transitions
Only approved roles may move a CR between states. Every transition is
logged with the actor and timestamp.

## Rejection and Rework
Rejected CRs are returned with reasons. Reworked CRs re-enter review
without losing history.

## Closure
A CR closes only after successful implementation, rollback readiness expiry
and documentation of outcomes.

Policy code: CR-LIFE-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "cr_templates",
 "title": "CR Templates & Mandatory Fields",
 "body": """
## Standard Template
- Change title and unique ID.
- Category: standard, normal, emergency.
- Business justification and impacted services.
- Risk assessment and rollback plan.
- Implementation window and owner.

## Field Completeness
A CR cannot be submitted with missing mandatory fields. The tool validates
completeness before routing.

## Evidence Attachments
Test results, approvals and communication drafts attach to the CR before
CAB review.

## Template Updates
Templates are reviewed annually by the Change Management Office.

Policy code: CR-TPL-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "emergency_change_process",
 "title": "Emergency Change Process",
 "body": """
## Definition
Emergency changes address production incidents requiring immediate
remediation, where waiting for CAB would extend impact.

## Initiation
The incident commander opens an emergency CR with the incident ID linked.

## Approval
Emergency approval requires two approvers from the on-call list, one of
whom is a manager or above.

## Retrospective
Every emergency change undergoes post-implementation review within 5
working days. Unplanned work is reported to CAB.

## Controls
Abuse of the emergency route (pre-planned work logged as emergency) is a
compliance breach.

Policy code: CR-EMER-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "change_calendar",
 "title": "Change Calendar Management",
 "body": """
## Purpose
The calendar sequences approved changes to avoid resource conflicts and
landing-zone contention.

## Slotting Rules
- No more than the prescribed number of production changes per window.
- Dependency-linked changes are scheduled together.
- High-risk changes are isolated from other high-risk changes.

## Conflict Resolution
Calendar conflicts are escalated to the Change Management Office, which
arbitrates based on business priority.

## Visibility
The calendar is published and visible to all delivery teams.

Policy code: CR-CAL-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "release_management_policy",
 "title": "Release Management Policy",
 "body": """
## Release Types
Major, minor and patch releases follow defined paths. Hotfixes use the
emergency change route.

## Release Train
Standard releases align to a scheduled release train with fixed windows.

## Entry Criteria
Code freeze adherence, test sign-off, rollback plan and runbooks are
entry criteria for production deployment.

## Post-Release
Release health is monitored for the defined period; defects are triaged
to hotfix or next release.

Policy code: CR-REL-2026-01 | Owner: Release Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "deployment_windows",
 "title": "Deployment Windows",
 "body": """
## Standard Windows
Production deployments run in the night maintenance window: 00:00 to
04:00 IST, unless otherwise approved.

## Exceptions
Customer-impacting daytime changes require business-head and CAB
approval with documented mitigation.

## Window Discipline
Deployments must complete within the window. Runaway deployments are
halted and rolled back per the runbook.

## Weekend Deployments
Weekend deployments are permitted only for approved releases and require
on-call support coverage.

Policy code: CR-WIN-2026-01 | Owner: Release Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "rollback_drills",
 "title": "Rollback & Recovery Drills",
 "body": """
## Drill Requirement
High-risk changes must have a rollback plan validated in a recent drill.

## Drill Types
- Tabletop: walkthrough of rollback steps and decision points.
- Technical: actual rollback execution in a staging environment.

## Frequency
Drills run at least quarterly for critical applications; evidence is
attached to the change.

## Gaps
Drill gaps are remediated before the change proceeds. Unremediated gaps
escalate to CAB.

Policy code: CR-RB-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "impact_assessment_checklist",
 "title": "Impact Assessment Checklist",
 "body": """
## Dimensions
- Customer: which journeys and channels are affected.
- Systems: upstream and downstream dependencies.
- Data: schema, migration and retention impact.
- Regulatory: reporting and audit implications.
- Operations: runbook and support readiness.

## Scoring
Changes are scored low, medium or high risk from the assessment. Score
drives the approval route.

## Review
Assessments are reviewed by a peer outside the delivery team for bias.

Policy code: CR-IA-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "change_approval_matrix",
 "title": "Change Approval Matrix",
 "body": """
## Approval Levels
- Standard: team lead.
- Normal, medium risk: CAB with business representative.
- Normal, high risk: CAB plus business head.
- Emergency: two on-call approvers.

## Segregation
Implementers cannot approve their own changes. Approvers must be outside
the delivery team.

## Evidence
Approvals are recorded in the tool with timestamps and approver identity.

## Delegation
Approval delegation is defined per role in the matrix and reviewed
annually.

Policy code: CR-APPR-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "change_freeze_calendar",
 "title": "Change Freeze Calendar",
 "body": """
## Freeze Periods
- Financial year-end: last 5 business days of March.
- Half-year close: last 3 business days of September.
- RBI-mandated reporting windows.
- Major festival sale periods for customer-facing systems.

## Exceptions
Freeze exceptions require CIO approval and must be logged as emergency
changes.

## Communication
The freeze calendar is published annually and revised as needed.

Policy code: CR-FREEZE-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "incident_to_change_linkage",
 "title": "Incident-to-Change Linkage",
 "body": """
## Mandatory Linkage
Every production change must reference a change record; every change
record must reference the motivating incident, problem or feature.

## Traceability
The tool enforces bi-directional links between incidents, problems and
changes for audit.

## Analysis
Unplanned change volume by root cause is reviewed monthly to drive
prevention.

## Reporting
The Change Management Office publishes incident-change linkage metrics
to CAB.

Policy code: CR-LINK-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "problem_management_policy",
 "title": "Problem Management Policy",
 "body": """
## Purpose
Problem management finds root causes behind recurring incidents and
prevents recurrence.

## Process
1. Trend analysis and problem identification.
2. Root-cause analysis with structured techniques.
3. Corrective action planning and ownership.
4. Verification and closure.

## Linkage
Problems link to related incidents and the changes that resolve them.

## Metrics
Recurrence rate, mean time to problem resolution and open-problem aging
are reviewed monthly.

Policy code: CR-PROB-2026-01 | Owner: IT Service Management.
"""
},
{
 "bubble": "CR",
 "slug": "post_implementation_review",
 "title": "Post-Implementation Review",
 "body": """
## Scope
Every normal and emergency change undergoes a post-implementation review.

## Review Questions
- Did the change achieve objectives without regression?
- Was the rollback plan needed; did it work?
- Were estimates accurate?
- What should be done differently?

## Timeline
Reviews complete within 5 working days for emergency and 10 working days
for normal changes.

## Outputs
Review outcomes update the risk register, templates and runbooks.

Policy code: CR-PIR-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "config_management_basics",
 "title": "Configuration Management Basics",
 "body": """
## CMDB Scope
The configuration management database records production assets, their
relationships and owners.

## CI Attributes
Each configuration item carries owner, environment, criticality, and
dependency attributes.

## Change Linkage
Changes must reference affected configuration items. The CMDB updates
on implementation.

## Accuracy
CMDB accuracy is measured quarterly; critical-item accuracy below the
threshold triggers remediation.

Policy code: CR-CMDB-2026-01 | Owner: IT Service Management.
"""
},
{
 "bubble": "CR",
 "slug": "environment_strategy",
 "title": "Environment Strategy",
 "body": """
## Environments
Dev, QA, staging and production with defined promotion rules.

## Parity
Staging mirrors production configuration for the change class being
tested. Drift is reconciled before deployment.

## Data
Test environments use masked or synthetic data. Production data in
non-production environments requires approval.

## Access
Environment access follows least privilege; production access is
break-glass controlled.

Policy code: CR-ENV-2026-01 | Owner: Release Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "test_evidence_requirements",
 "title": "Test Evidence Requirements",
 "body": """
## Required Evidence
- Unit and integration test results.
- UAT sign-off by business stakeholders.
- Performance test results for changes affecting critical paths.
- Regression suite outcome.

## Standards
Evidence must be attributable (tester, environment, date) and attached
to the change record.

## Sampling
The Change Management Office samples evidence for quality; gaps return
the change to review.

Policy code: CR-TEST-2026-01 | Owner: Quality Assurance.
"""
},
{
 "bubble": "CR",
 "slug": "cab_roles_and_responsibilities",
 "title": "CAB Roles & Responsibilities",
 "body": """
## Chair
The CAB chair convenes meetings, arbitrates conflicts and owns the
agenda.

## Members
Representatives from infrastructure, applications, security, business
units and the service desk.

## Duties
- Review and approve changes within authority.
- Review emergency-change retrospectives.
- Escalate policy violations.

## Cadence
Standing CAB meets twice weekly; emergency CAB convenes on demand.

Policy code: CR-CAB-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "cr_kpi_metrics",
 "title": "CR KPIs & Metrics",
 "body": """
## Key Metrics
- Successful change rate.
- Unplanned/emergency change ratio.
- Change-induced incident rate.
- Post-implementation review completion.
- Calendar adherence.

## Targets
Targets are set annually by the Change Management Office and reviewed
with CAB monthly.

## Reporting
A monthly change dashboard is published to senior management.

## Drill-Down
Metrics drill to individual changes for root-cause analysis.

Policy code: CR-KPI-2026-01 | Owner: Change Management Office.
"""
},
{
 "bubble": "CR",
 "slug": "change_automation_guidelines",
 "title": "Change Automation Guidelines",
 "body": """
## Scope
Automation covers CI/CD deployment pipelines, infrastructure-as-code and
self-service standard changes.

## Governance
Automated changes remain governed by the same approval matrix; standard
changes may use pre-approved templates.

## Guardrails
- Automated tests as gates.
- Immutable audit logs.
- Automatic rollback triggers on failure thresholds.

## Exclusions
High-risk and regulatory-impacting changes remain manual unless
specifically approved for automation.

Policy code: CR-AUTO-2026-01 | Owner: DevOps Enablement.
"""
},
{
 "bubble": "CR",
 "slug": "audit_trail_requirements",
 "title": "Audit Trail Requirements for Changes",
 "body": """
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
"""
},
]
