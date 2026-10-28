"""CONVERSATIONAL_BI + GENERAL corpora.

BI content covers architecture, governance and data practices in synthetic
terms; general content is the ADI assistant's own meta-documentation. Original prose.
"""

DOCS = [
# ================================================================ CONVERSATIONAL_BI
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_platform_architecture",
 "title": "BI Platform Architecture",
 "body": """
## Layers
1. Sources: core banking, CRM, cards, payments and HR systems.
2. Lakehouse: raw, curated and semantic layers on the analytics platform.
3. Serving: semantic models consumed by dashboards, notebooks and the
   conversational BI assistant.

## Data Flow
Change-data-capture and batch pipelines land data within defined freshness
SLAs. Transformations produce the curated and semantic layers.

## Access Paths
The conversational BI assistant reads only the semantic layer. No query
touches source systems directly.

## Resilience
Pipelines carry retries, dead-letter handling and data-quality gates.

Policy code: BI-ARCH-2026-01 | Owner: Data Platform team.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_data_models",
 "title": "BI Data Models",
 "body": """
## Subject Areas
- Liabilities and assets (CASA, deposits, loans).
- Cards (spends, payments, rewards).
- Payments (UPI, NEFT/RTGS, mandates).
- Customer 360 (demographics, products, interactions).
- Branch and channel performance.
- HR and workforce metrics.

## Modelling Conventions
Fact tables use additive measures; dimensions conform across subject areas.
Calendar is the common conformed dimension.

## Definitions
Every measure carries an approved definition, owner and refresh timestamp
visible in the data dictionary.

Policy code: BI-MODEL-2026-01 | Owner: Data Platform team.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_query_guardrails",
 "title": "Query Guardrails for Conversational BI",
 "body": """
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
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_sample_queries",
 "title": "Sample Conversational Queries",
 "body": """
## Customer Metrics
"Show savings account balance trend for the last six months by region."

## Cards
"What was credit card spend last quarter compared to the previous quarter?"

## Branch Performance
"List the bottom five branches by current-account acquisition this month."

## Payments
"How many UPI transactions failed yesterday by failure code?"

## HR
"Show attrition rate for grade AVP and above in the last two quarters."

## Tips
Mention the measure, dimension and time window explicitly for best results.

Policy code: BI-QUERY-2026-01 | Owner: Data Platform team.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_kpi_definitions",
 "title": "KPI Definitions",
 "body": """
## Business KPIs
- CASA ratio: CASA deposits / total deposits.
- Net interest margin: net interest income / average interest-earning assets.
- Credit cost: provisions / average advances.
- Cost-to-income: operating expenses / operating income.

## Customer KPIs
- Active rate: active customers / total customers over 90 days.
- Digital adoption: digital transactors / active customers.
- Net promoter score: promoters minus detractors, survey-based.

## Quality Rules
KPIs are versioned. Changes are approved by the KPI governance council.

Policy code: BI-KPI-2026-01 | Owner: Business Analytics CoE.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_dashboards",
 "title": "Dashboard Catalogue",
 "body": """
## Executive
Daily performance snapshot: balances, disbursals, transactions and
exceptions.

## Business Line Dashboards
- Retail assets: disbursement, delinquency, collections.
- Cards: acquisition, spends, rewards, attrition.
- Payments: success rates, failures, chargebacks.

## Support Dashboards
- Data quality and pipeline health.
- Conversational BI usage and answer accuracy.

## Access
Dashboards are role-scoped. New dashboards follow the reporting request
workflow.

Policy code: BI-DASH-2026-01 | Owner: Business Analytics CoE.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_data_freshness",
 "title": "Data Freshness SLAs",
 "body": """
## Tiers
- T0 (real-time/near-real-time): payment and fraud views, up to 15 minutes.
- T1 (daily): business performance and customer metrics, by 09:00 IST.
- T2 (weekly/monthly): HR and survey aggregates.

## Visibility
Each dashboard shows its last refresh timestamp. The assistant quotes
data-as-of dates in answers.

## Breach Handling
Freshness breaches alert the data engineering on-call and are tracked to
resolution.

Policy code: BI-FRESH-2026-01 | Owner: Data Platform team.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_row_level_security",
 "title": "Row-Level Security",
 "body": """
## Purpose
Row-level security ensures users see only the data their role permits.

## Dimensions
- Geography: zone, region, branch.
- Business: product lines and segments.
- Customer tiers: priority, retail, SME.

## Enforcement
RLS is enforced in the semantic layer, so dashboards and the assistant
inherit identical restrictions.

## Changes
RLS changes route through the data access request workflow with owner
approval.

Policy code: BI-RLS-2026-01 | Owner: Data Governance.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_governance",
 "title": "BI Governance Framework",
 "body": """
## Roles
- Data owners: accountable for definitions and quality.
- Data stewards: maintain the dictionary and lineage.
- BI consumers: use approved assets only.

## Change Control
Metric definitions, model changes and new dashboards follow the change
board process with impact assessment.

## Quality
Data-quality rules run at load. Scores publish on the quality dashboard.

## Review
The BI governance council reviews assets, usage and access quarterly.

Policy code: BI-GOV-2026-01 | Owner: Data Governance.
"""
},
{
 "bubble": "CONVERSATIONAL_BI",
 "slug": "bi_training_guide",
 "title": "Conversational BI Training Guide",
 "body": """
## Getting Started
Start with the sample questions and the data dictionary walkthrough.

## Asking Better Questions
- Name the measure: balance, disbursal, spend, activation.
- Add dimensions: region, branch, product, month.
- State the window: yesterday, last quarter, FY-to-date.

## Understanding Answers
Answers cite the semantic model and data-as-of timestamp. Verify unusual
results against the source dashboard.

## Support
Queries, feedback and corrections route through the BI support queue.

Policy code: BI-TRAIN-2026-01 | Owner: Business Analytics CoE.
"""
},
# ================================================================ GENERAL
{
 "bubble": "GENERAL",
 "slug": "vartalaap_overview",
 "title": "वार्तालाप (Vartalaap) Assistant Overview",
 "body": """
## What It Is
वार्तालाप is the bank's internal AI assistant that answers policy, product,
process and analytics questions by searching approved internal knowledge.

## How It Works
Questions are matched against indexed documents; relevant passages are
retrieved and used to compose grounded answers with citations.

## Capabilities
- Policy lookup across HR, IT, legal, ops and finance.
- Product and process guidance from the knowledge base.
- Analytics questions answered from curated BI models.

## Channels
Available as a chat assistant on the intranet and via the API for embedded
experiences.

Policy code: GEN-OV-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "vartalaap_getting_started",
 "title": "Getting Started with वार्तालाप",
 "body": """
## Login
Use your employee ID and corporate credentials. First-time users complete
a short preference setup.

## Asking Questions
- Write complete, specific questions.
- Mention the context: policy name, product or system.
- One topic per question works best.

## Reading Answers
Answers include cited sources. Click a source to open the document.

## Feedback
Use the thumbs-up or thumbs-down on every answer to improve the assistant.

Policy code: GEN-START-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "bubbles_explained",
 "title": "वार्तालाप Bubbles Explained",
 "body": """
## What Are Bubbles
Bubbles are knowledge domains the assistant searches: HR, LAW, IT Helpdesk,
Financial Advisor, Conversational BI, Download, Aha, Axis Phone, Change
Requests and General.

## Choosing a Bubble
Select a bubble to scope the answer to that domain. Leave unselected to
search all domains.

## Bubble Owners
Each bubble has an owner who curates documents and reviews feedback.

## New Bubbles
Proposals for new bubbles route through the ADI Program Office.

Policy code: GEN-BUB-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "vartalaap_faq",
 "title": "वार्तालाप Frequently Asked Questions",
 "body": """
## Common Questions
Q: Is my conversation private?
A: Conversations are logged for audit with your user ID; sensitive data is
masked in logs.

Q: Can it see customer PII?
A: Retrieval uses approved internal documents. Customer PII is masked in
answers per data policy.

Q: Why no answer?
A: The question may be outside the knowledge base. Try rephrasing or use a
different bubble.

Q: How accurate is it?
A: Answers cite sources. Verify critical decisions against the source
document.

Policy code: GEN-FAQ-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "privacy_notice",
 "title": "वार्तालाप Privacy Notice",
 "body": """
## Data Collected
User ID, questions, answers, feedback and interaction timestamps.

## Use of Data
Data is used to answer queries, improve the assistant and monitor usage.
Answers quality is reviewed by bubble owners.

## Retention
Conversation logs are retained per the records policy and purged on
schedule.

## Your Choices
You can request deletion of your feedback records through the privacy
desk. Questions needed for audit are retained.

Policy code: GEN-PRIV-2026-01 | Owner: Data Protection Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "usage_guidelines",
 "title": "वार्तालाप Usage Guidelines",
 "body": """
## Appropriate Use
- Internal policy, product and process questions.
- Analytics questions from approved BI models.
- Drafting support for routine internal communication.

## Inappropriate Use
- Customer PII lookups outside authorised processes.
- Generating content for external release without approval.
- Circumventing approvals or controls.

## Accountability
Users remain responsible for decisions. Assistant output is a starting
point, not a substitute for policy documents.

Policy code: GEN-USE-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "limitations_and_disclaimers",
 "title": "वार्तालाप Limitations & Disclaimers",
 "body": """
## Limitations
- Knowledge is limited to indexed documents and their freshness dates.
- Answers may lag the latest circulars until re-indexing.
- Numeric answers should be cross-checked against source systems.

## Disclaimers
- The assistant does not make decisions on your behalf.
- Legal and tax content is informational; consult the owning team for
  definitive positions.

## Escalation
For incorrect answers, use the feedback buttons and flag the owning team.

Policy code: GEN-LIM-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "banking_glossary",
 "title": "Banking Glossary",
 "body": """
## Core Terms
- CASA: current account savings account.
- NPA: non-performing asset.
- CRR / SLR: cash reserve ratio / statutory liquidity ratio.
- MCLR: marginal cost of funds based lending rate.
- CDR: credit deposit ratio.

## Payments
- NEFT / RTGS / UPI / IMPS: funds transfer systems.
- NACH / ECS: mandate-based clearing.
- CTS: cheque truncation system.

## Compliance
- KYC, AML, PMLA, FIU-IND, STR, CTR, PEP.

Policy code: GEN-GLOSS-B-2026-01 | Owner: Learning & Development.
"""
},
{
 "bubble": "GENERAL",
 "slug": "hr_glossary",
 "title": "HR Glossary",
 "body": """
## Employment
- CTC: cost to company.
- LPA: lakhs per annum.
- Probation: initial assessment period.
- Notice period: service continuation after resignation.

## Rewards
- Variable pay: performance-linked component.
- Retirals: PF, gratuity, superannuation.
- Perquisites: non-cash benefits.

## Processes
- PIP: performance improvement plan.
- IJP: internal job posting.
- POSH: prevention of sexual harassment.

Policy code: GEN-GLOSS-H-2026-01 | Owner: Learning & Development.
"""
},
{
 "bubble": "GENERAL",
 "slug": "acronym_dictionary",
 "title": "Acronym Dictionary",
 "body": """
## Business
- AUM: assets under management.
- NIM: net interest margin.
- ROA: return on assets.
- SLA: service level agreement.

## Technology
- VPN: virtual private network.
- MFA: multi-factor authentication.
- CMDB: configuration management database.
- VAPT: vulnerability assessment and penetration testing.

## Governance
- CAB: change advisory board.
- PIR: post-implementation review.
- BCP: business continuity plan.
- DPO: data protection officer.

Policy code: GEN-ACRO-2026-01 | Owner: Learning & Development.
"""
},
{
 "bubble": "GENERAL",
 "slug": "escalation_contacts",
 "title": "Escalation Contacts Directory",
 "body": """
## IT
- Service desk: ext. 5000 or the Unidesk portal.
- Security incidents: security operations hotline.

## HR
- Employee services helpdesk: HR portal.
- Grievance officer: grievance inbox.

## Compliance & Legal
- Compliance helpline for policy queries.
- Legal intake for notices and contracts.

## Facilities
- Facility helpdesk for infrastructure issues.

Note: contact details live in the corporate directory; do not share
externally.

Policy code: GEN-ESC-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "GENERAL",
 "slug": "helpdesk_directory",
 "title": "Helpdesk Directory",
 "body": """
## Purpose
One list of every internal service desk and their scope.

## Entries
- IT Helpdesk: hardware, software, access, VPN.
- HR Helpdesk: leave, payroll, reimbursements, benefits.
- Facility Desk: seating, power, housekeeping.
- Compliance Desk: policy interpretation and declarations.
- Data Desk: access requests and BI support.

## Etiquette
Provide employee ID, location and ticket references when following up.

Policy code: GEN-DIR-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "GENERAL",
 "slug": "internal_news",
 "title": "Internal News & Announcements",
 "body": """
## Channel
The intranet news feed publishes leadership notes, circulars and event
invitations.

## Categories
- Business updates and results.
- People announcements.
- Technology and process changes.
- Compliance reminders.

## Retrieval
वार्तालाप can surface recent announcements. For dated facts, always check
the publication date.

Policy code: GEN-NEWS-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "GENERAL",
 "slug": "training_index",
 "title": "Training Catalogue Index",
 "body": """
## Mandatory Training
- AML and KYC refresher (annual).
- Information security awareness (annual).
- POSH awareness (periodic).
- Code of conduct (onboarding and annual).

## Role-Based
- Credit underwriting academy.
- Contact-centre certification.
- Conversational BI and data literacy.

## Enrollment
Enroll via the learning management system. Completions are tracked in the
employee profile.

Policy code: GEN-TRAIN-2026-01 | Owner: Learning & Development.
"""
},
{
 "bubble": "GENERAL",
 "slug": "km_portal_guide",
 "title": "Knowledge Management Portal Guide",
 "body": """
## Content Types
Policies, process documents, one-pagers, FAQs and training material.

## Browsing
Browse by bubble, department or document type. Use filters for owner and
recency.

## Contributing
Propose new documents through the owning team. Every document has an
owner and review date.

## Search Tips
Use exact terms from the document. Combine department and topic keywords.

Policy code: GEN-KM-2026-01 | Owner: Corporate Communications.
"""
},
{
 "bubble": "GENERAL",
 "slug": "search_tips",
 "title": "Search Tips for वार्तालाप",
 "body": """
## Be Specific
Prefer "laptop refresh policy" over "computer rules".

## Use Policy Names
Mention the policy or form code when known, e.g. HR-LEAVE-01.

## One Question at a Time
Split compound questions for more precise answers.

## Follow Up
Use follow-up questions to narrow down: "What about employees on
probation?"

## Check Sources
Open the cited document to verify details before acting.

Policy code: GEN-SEARCH-2026-01 | Owner: ADI Program Office.
"""
},
{
 "bubble": "GENERAL",
 "slug": "document_standards",
 "title": "Document Standards for Knowledge Base",
 "body": """
## Format
Markdown with a title, section headings and a policy code footer.

## Structure
- Scope and purpose first.
- Rules and steps.
- Exceptions and escalation.
- Owner and review date.

## Style
Plain language, short paragraphs, numbered steps for procedures.

## Metadata
Every document carries bubble, owner, effective date and version.

Policy code: GEN-DOC-2026-01 | Owner: Process Governance.
"""
},
{
 "bubble": "GENERAL",
 "slug": "rbi_reading_list",
 "title": "RBI Circulars Reading List",
 "body": """
## Key Frameworks
- KYC Master Direction (as amended).
- Cyber-security framework for banks.
- Digital lending guidelines.
- Outsourcing directions.
- Fair practices code for lending.

## Where to Read
Full circulars are available on the RBI website. The bank's compliance
intranet summarises applicability.

## Usage
Use summaries for awareness; rely on the owning team for interpretation.

Policy code: GEN-RBI-2026-01 | Owner: Compliance.
"""
},
{
 "bubble": "GENERAL",
 "slug": "learning_paths",
 "title": "Learning Paths",
 "body": """
## New Joiner Path
Onboarding, code of conduct, security basics and the assistant's getting
started guide.

## Branch Banking Path
KYC, service standards, fraud watch and customer grievance handling.

## Analytics Path
Data literacy, conversational BI training and dashboard certification.

## Leadership Path
Governance essentials, risk management and people-management modules.

Policy code: GEN-LP-2026-01 | Owner: Learning & Development.
"""
},
{
 "bubble": "GENERAL",
 "slug": "process_governance_guide",
 "title": "Process Governance Guide",
 "body": """
## Document Lifecycle
Draft, review, approve, publish, revise and retire. Every stage has
defined owners.

## Change Triggers
Regulatory updates, audit findings, incident lessons and annual reviews
trigger revisions.

## Approval
Policies require the process owner plus compliance review. Publishing
without approval is a breach.

## Retirement
Superseded documents are archived with a pointer to the successor.

Policy code: GEN-GOV-2026-01 | Owner: Process Governance.
"""
},
{
 "bubble": "GENERAL",
 "slug": "service_standards",
 "title": "Internal Service Standards",
 "body": """
## Response SLAs
- IT incidents: P1 2 hours, P2 8 hours, P3 2 business days.
- HR queries: 2 business days.
- Compliance interpretations: 5 business days.

## Quality
Every desk confirms resolution with the requester before closure.

## Feedback
Rate internal services through the monthly pulse or ticket surveys.

## Escalation
Missed SLAs escalate to the desk lead automatically.

Policy code: GEN-SLA-2026-01 | Owner: Process Governance.
"""
},
]
