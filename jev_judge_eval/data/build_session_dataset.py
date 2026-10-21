"""Generate 100 synthetic ADI sessions containing exactly 250 query turns.

Writes:
    synthetic_adi_gt_100_sessions_250_queries.csv
    synthetic_adi_gt_100_sessions_250_queries_gold.csv

The SME-compatible columns are retained. Session ID, turn position, session length,
and JSON prior-turn history are added so session-level analysis is possible.
All records, people, policies, identifiers and data are fictional.

The currently shipped judge scripts score each row independently and ignore the added
history column. Use this dataset for session-aware judging only after explicitly adding
history to both judge inputs.

Usage:
    python data/build_session_dataset.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "synthetic_adi_gt_100_sessions_250_queries.csv"
GOLD_CSV = HERE / "synthetic_adi_gt_100_sessions_250_queries_gold.csv"

SME_COLUMNS = [
    "User Query",
    "Response by ADI",
    "Content Retrieved by ADI",
    "Use case Tagged by ADI",
    "Product Tagged by ADI",
    "Subproduct Tagged by ADI",
    "Subproduct Tagged by ADI - comment",
    "Document Name Retrieved by ADI",
    "SME Employee ID",
    "Is ADI response Correct? (Yes/No)",
    "If ADI response incorrect(Enter right response)",
    "Document Name(s) Expected to be Referred",
]
EXTRA_COLUMNS = [
    "Product as per SME",
    "Subproduct as per SME",
    "Session ID",
    "Session Turn",
    "Session Length",
    "Prior Conversation (JSON)",
]
DATA_COLUMNS = SME_COLUMNS + EXTRA_COLUMNS
GOLD_COLUMNS = [
    "row_id",
    "session_id",
    "session_turn",
    "user_query",
    "scenario",
    "gold_faithful",
    "gold_answer_relevant",
    "gold_context_relevant",
    "gold_toxic",
    "gold_tone_professional",
    "gold_answer_correctness",
]

# Each domain thread has three standalone, naturally connected questions.
# Every answer contains a numeric fact so the deterministic key-figure fault can
# change one supported fact without inventing unrelated product content.
TOPICS = [
    {
        "domain": "HR", "product": "HR", "subproduct": "Leave Policy",
        "doc": "HR_Leave_Policy_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: HR_Leave_Policy_FY27.pdf | Casual Leave] Employees receive 12 days of Casual Leave (CL) per calendar year, pro-rated on joining. CL is not carried forward or encashed. A maximum of 3 consecutive CL days may be taken at once.",
        "qas": [
            ("How many casual leave days do employees receive each year?", "Employees receive 12 days of Casual Leave per calendar year, pro-rated on joining."),
            ("Can unused casual leave be carried forward or encashed?", "Unused Casual Leave is not carried forward or encashed; the annual entitlement is 12 days."),
            ("What is the longest continuous casual-leave period?", "Employees may take up to 3 consecutive Casual Leave days at a time."),
        ],
        "false_fact": "Unused Casual Leave can also be encashed at year end.",
    },
    {
        "domain": "HR", "product": "HR", "subproduct": "PF & Gratuity",
        "doc": "HR_PF_Gratuity_Handbook_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: HR_PF_Gratuity_Handbook_FY27.pdf | Gratuity] Gratuity is payable on separation after 5 years of continuous service, except in death or disablement cases. The calculation uses 15 days of last-drawn Basic salary for each completed year of service.",
        "qas": [
            ("How long must an employee serve to qualify for gratuity?", "Gratuity normally requires 5 years of continuous service; the condition does not apply in death or disablement cases."),
            ("How is gratuity calculated for each completed year?", "The calculation uses 15 days of last-drawn Basic salary for each completed year of service."),
            ("Does the 5-year condition apply in a disablement case?", "No. The 5-year service condition does not apply in disablement cases."),
        ],
        "false_fact": "Employees with 3 years of service also receive a partial gratuity payment.",
    },
    {
        "domain": "DOWNLOAD", "product": "Social Security Schemes", "subproduct": "PMSBY",
        "doc": "SSS_PMSBY_Enrolment_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: SSS_PMSBY_Enrolment_SOP_FY27.pdf | Eligibility and Enrolment] Eligible customers are aged 18 to 70 and hold an active savings account. The annual premium is Rs. 20, auto-debited on or before 31 May. Branch staff obtain consent and nominee details before enrolment.",
        "qas": [
            ("What is the age eligibility for PMSBY?", "PMSBY is available to eligible savings-account customers aged 18 to 70."),
            ("What is the annual PMSBY premium and when is it debited?", "The annual PMSBY premium is Rs. 20 and is auto-debited on or before 31 May."),
            ("What should branch staff collect before enrolling a customer?", "Staff should confirm the active savings account and age 18 to 70, then obtain the customer's consent and nominee details."),
        ],
        "false_fact": "Customers up to age 75 are eligible and the annual premium is Rs. 40.",
    },
    {
        "domain": "LAW", "product": "NR Banking", "subproduct": "NRO Savings",
        "doc": "NR_NRO_Savings_Product_Note_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: NR_NRO_Savings_Product_Note_FY27.pdf | Average Monthly Balance] NRO savings accounts require an Average Monthly Balance of Rs. 25,000 in metro and urban branches, and Rs. 10,000 in semi-urban and rural branches. Non-maintenance charges are 5% of the shortfall, capped at Rs. 600 per month.",
        "qas": [
            ("What is the NRO savings AMB in metro branches?", "The NRO savings Average Monthly Balance for metro and urban branches is Rs. 25,000."),
            ("What NRO savings AMB applies in semi-urban branches?", "The NRO savings Average Monthly Balance for semi-urban and rural branches is Rs. 10,000."),
            ("How are NRO non-maintenance charges calculated?", "The charge is 5% of the AMB shortfall and is capped at Rs. 600 per month."),
        ],
        "false_fact": "The metro NRO minimum is Rs. 10,000 and the monthly charge cap is Rs. 1,000.",
    },
    {
        "domain": "LAW", "product": "NR Banking", "subproduct": "NRE Savings",
        "doc": "NR_NRE_Savings_Product_Note_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: NR_NRE_Savings_Product_Note_FY27.pdf | Average Monthly Balance] NRE savings accounts require an Average Monthly Balance of Rs. 10,000 in metro and urban branches and Rs. 5,000 in semi-urban and rural branches. NRE funds are repatriable, subject to applicable rules.",
        "qas": [
            ("What is the NRE savings AMB in metro branches?", "The NRE savings Average Monthly Balance for metro and urban branches is Rs. 10,000."),
            ("What is the NRE savings minimum in rural branches?", "The NRE savings Average Monthly Balance for semi-urban and rural branches is Rs. 5,000."),
            ("Can NRE savings funds be repatriated?", "NRE savings funds are repatriable, subject to applicable rules; the metro AMB is Rs. 10,000."),
        ],
        "false_fact": "NRE balances cannot be repatriated and the rural minimum is Rs. 10,000.",
    },
    {
        "domain": "DOWNLOAD", "product": "Retail Loans", "subproduct": "Home Loan",
        "doc": "Retail_Assets_Home_Loan_Policy_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Retail_Assets_Home_Loan_Policy_FY27.pdf | Prepayment] No prepayment charges apply to floating-rate home loans for individual borrowers, whether paid from own funds or via balance transfer. Fixed-rate balance-transfer foreclosure attracts 2% of principal outstanding.",
        "qas": [
            ("Are floating-rate home loans subject to prepayment charges?", "No prepayment charges apply to individual borrowers on floating-rate home loans."),
            ("Does the no-charge rule also cover a balance transfer?", "Yes. No charge applies to a floating-rate individual home loan paid through balance transfer."),
            ("What foreclosure charge applies to fixed-rate balance transfer?", "A fixed-rate home loan closed through balance transfer attracts 2% of principal outstanding."),
        ],
        "false_fact": "Floating-rate home-loan prepayment attracts a 2% charge.",
    },
    {
        "domain": "DOWNLOAD", "product": "Cards", "subproduct": "Debit Card Reissue",
        "doc": "Cards_Debit_Card_Reissue_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Cards_Debit_Card_Reissue_SOP_FY27.pdf | Duplicate Card] Branch requests for a duplicate debit card are dispatched to the registered address within 7 working days. The Rs. 200 plus GST reissue fee is waived for Burgundy and Priority customers.",
        "qas": [
            ("How long does a branch duplicate debit card request take?", "A branch duplicate debit card request is dispatched within 7 working days."),
            ("What fee applies to a duplicate debit card?", "The duplicate debit card reissue fee is Rs. 200 plus GST, unless the customer is Burgundy or Priority."),
            ("Do Burgundy customers pay the debit-card reissue charge?", "No. The Rs. 200 plus GST reissue fee is waived for Burgundy customers."),
        ],
        "false_fact": "Every replacement debit card is dispatched within 2 working days for a Rs. 500 fee.",
    },
    {
        "domain": "IT_HELPDESK", "product": "IT Helpdesk", "subproduct": "VPN Access",
        "doc": "IT_VPN_Access_Guide_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: IT_VPN_Access_Guide_FY27.pdf | Password Reset] VPN credentials synchronize with the domain password. Reset through the SSPR portal using the OTP sent to the registered mobile, then set a password meeting complexity policy. Synchronization to VPN takes up to 15 minutes.",
        "qas": [
            ("How do I reset my VPN password?", "Reset the synchronized domain password through SSPR using the registered-mobile OTP; allow up to 15 minutes for VPN sync."),
            ("Where is the OTP sent during an SSPR reset?", "The SSPR verification OTP is sent to the registered mobile number."),
            ("How long should I wait for the reset password to sync to VPN?", "The new domain password should synchronize to VPN within 15 minutes."),
        ],
        "false_fact": "VPN password synchronization can take up to 48 hours.",
    },
    {
        "domain": "STATUS", "product": "Cards", "subproduct": "Service Request Status",
        "doc": "Unidesk_SR_Lookup_API", "use_case": "Status Retrieval",
        "context": "[API: Unidesk SR Lookup] Synthetic SR {reference}: category Debit Card Replacement; status In Progress; owner Cards Ops Dispatch; last updated 29 Sep 2026; target closure 3 Oct 2026.",
        "qas": [
            ("What is the current status of SR {reference}?", "SR {reference} for debit-card replacement is In Progress with Cards Ops Dispatch; target closure is 3 Oct 2026."),
            ("Which team owns SR {reference}?", "Cards Ops Dispatch owns SR {reference}; its current status is In Progress."),
            ("What is the expected closure date for SR {reference}?", "The expected closure date for SR {reference} is 3 Oct 2026."),
        ],
        "false_fact": "SR {reference} is Resolved and was closed on 1 Oct 2026.",
    },
    {
        "domain": "STATUS", "product": "Cards", "subproduct": "Credit Card Application",
        "doc": "PrimeCTL_Application_Lookup_API", "use_case": "Status Retrieval",
        "context": "[API: PrimeCTL Application Lookup] Synthetic application {reference}: Pending at Credit Underwriting due to an income-document discrepancy; re-upload requested 30 Sep 2026; owner CPU Underwriting Team.",
        "qas": [
            ("What is the status of application {reference}?", "Application {reference} is Pending at Credit Underwriting because of an income-document discrepancy."),
            ("Who owns the review for application {reference}?", "The CPU Underwriting Team owns application {reference}; a document re-upload was requested 30 Sep 2026."),
            ("What action is pending for application {reference}?", "An income document re-upload is pending for application {reference}; its status is Pending at Credit Underwriting."),
        ],
        "false_fact": "Application {reference} has been approved and dispatched for delivery.",
    },
    {
        "domain": "CONVERSATIONAL_BI", "product": "CASA", "subproduct": "Dormant Accounts",
        "doc": "Synthetic_Finacle_Accounts_Query", "use_case": "Text2SQL",
        "context": "[Text2SQL synthetic database] For branch Mumbai-Fort there are 37 dormant savings accounts. The synthetic table contains 120 savings accounts in total, of which 83 are active. Counts are test fixtures, not customer data.",
        "qas": [
            ("How many dormant savings accounts are in Mumbai-Fort?", "There are 37 dormant savings accounts in the synthetic Mumbai-Fort data."),
            ("How many savings accounts are active in the test data?", "There are 83 active savings accounts in the synthetic test data."),
            ("What is the total number of savings accounts in that test branch?", "The synthetic Mumbai-Fort fixture contains 120 savings accounts in total."),
        ],
        "false_fact": "The synthetic branch contains 47 dormant accounts and 93 active accounts.",
    },
    {
        "domain": "LAW", "product": "Compliance", "subproduct": "Re-KYC",
        "doc": "Compliance_ReKYC_Periodic_Update_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Compliance_ReKYC_Periodic_Update_SOP_FY27.pdf | Documents] With no KYC changes, a self-declaration through registered email, mobile, ATM, internet banking or letter is sufficient. A changed address requires a self-declaration and an OVD, verified within 2 months.",
        "qas": [
            ("What can a customer submit if their KYC details are unchanged?", "For unchanged KYC details, a self-declaration through registered email, mobile, ATM, internet banking or letter is sufficient."),
            ("What is needed if the customer's address has changed?", "Submit a self-declaration of the new address and an OVD; verify the change within 2 months."),
            ("How soon must the new-address OVD be verified?", "The new-address OVD should be verified within 2 months."),
        ],
        "false_fact": "An address change can be verified within 12 months without an OVD.",
    },
    {
        "domain": "DOWNLOAD", "product": "Deposits", "subproduct": "Fixed Deposit",
        "doc": "Deposits_FD_Premature_Withdrawal_Note_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Deposits_FD_Premature_Withdrawal_Note_FY27.pdf | Penalty] For fixed deposits below Rs. 5 crore, premature closure attracts a 1% penalty on the rate applicable for the period held. Senior Citizen Care FDs closed after 5 years have no penalty.",
        "qas": [
            ("What penalty applies to premature closure below Rs. 5 crore?", "A fixed deposit below Rs. 5 crore has a 1% rate penalty based on the period it remained with the bank."),
            ("Is there a penalty on Senior Citizen Care FD closure after 5 years?", "No penalty applies to a Senior Citizen Care fixed deposit closed after 5 years."),
            ("What deposit size does this premature-closure rule cover?", "The stated 1% penalty rule applies to fixed deposits below Rs. 5 crore."),
        ],
        "false_fact": "The premature-closure penalty is 2% and applies even after 5 years.",
    },
    {
        "domain": "CR", "product": "Operations", "subproduct": "NACH Mandate",
        "doc": "Ops_NACH_Mandate_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Ops_NACH_Mandate_SOP_FY27.pdf | Registration] Obtain signatures as per account operation mode, verify them against CBS, scan and upload in NACH Portal > Mandate Management > Create. Status is updated within 7 working days.",
        "qas": [
            ("How do I register a NACH mandate at the branch?", "Verify the signed mandate against CBS and upload it in NACH Portal > Mandate Management > Create."),
            ("Where is the signed NACH form uploaded?", "Upload the signed and verified form in the NACH Portal under Mandate Management > Create."),
            ("How long does NACH registration status take to update?", "The NACH registration status is updated within 7 working days."),
        ],
        "false_fact": "The mandate is active within 24 hours and a Rs. 100 fee is collected.",
    },
    {
        "domain": "GENERAL", "product": "CRES", "subproduct": "Meeting Rooms",
        "doc": "CRES_Workplace_Services_Guide_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: CRES_Workplace_Services_Guide_FY27.pdf | Meeting Rooms] Book in Workspace > Book > Meeting Room up to 14 days in advance, maximum 3 hours per slot. Check in within 15 minutes or the booking is auto-released.",
        "qas": [
            ("Where do I book a corporate meeting room?", "Book a meeting room in Workspace > Book > Meeting Room."),
            ("How early can I book and how long is each meeting slot?", "Bookings can be made up to 14 days ahead, for a maximum of 3 hours per slot."),
            ("When is a meeting-room reservation auto-released?", "A room is auto-released if you do not check in within 15 minutes of the start time."),
        ],
        "false_fact": "Meeting rooms can be booked 30 days ahead for 5-hour slots.",
    },
    {
        "domain": "HR", "product": "CASA", "subproduct": "Salary Account",
        "doc": "CASA_Salary_Account_Conversion_Note_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: CASA_Salary_Account_Conversion_Note_FY27.pdf | Conversion] Without salary credit for 3 consecutive months, the account converts to Easy Access savings and a Rs. 12,000 AMB applies. The employee can also request conversion at a branch using the Account Conversion Request form.",
        "qas": [
            ("When does a salary account become a regular savings account?", "After 3 consecutive months without salary credit, it converts to Easy Access savings with Rs. 12,000 AMB."),
            ("What minimum balance applies after salary-account conversion?", "The Easy Access savings account has a Rs. 12,000 Average Monthly Balance requirement."),
            ("Can I request salary-account conversion at a branch?", "Yes. Submit the Account Conversion Request form at a branch; automatic conversion follows 3 months without salary credit."),
        ],
        "false_fact": "The conversion occurs after 6 months and the new AMB is Rs. 5,000.",
    },
    {
        "domain": "FINANCIAL_ADVISOR", "product": "Forex", "subproduct": "LRS Outward Remittance",
        "doc": "Forex_Outward_Remittance_LRS_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Forex_Outward_Remittance_LRS_SOP_FY27.pdf | Limits] Resident individuals may remit up to USD 250,000 per financial year under LRS for permitted purposes, including education. TCS follows prevailing tax rules; a concessional rate applies for education financed through a financial-institution loan.",
        "qas": [
            ("What is the annual LRS remittance limit?", "The LRS limit is USD 250,000 per resident individual per financial year."),
            ("Can LRS be used for education abroad?", "Yes. Education is a permitted LRS purpose within the USD 250,000 annual limit."),
            ("Does education-loan funding affect LRS TCS?", "A concessional TCS rate applies when education remittance is financed by a financial-institution loan; the LRS limit is USD 250,000 per year."),
        ],
        "false_fact": "The annual LRS limit is USD 500,000 and education is excluded.",
    },
    {
        "domain": "DOWNLOAD", "product": "Operations", "subproduct": "Safe Deposit Locker",
        "doc": "Ops_Locker_Rent_Schedule_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Ops_Locker_Rent_Schedule_FY27.pdf | Metro Branches] Annual rent for a medium locker in a metro branch is Rs. 6,000 plus GST, payable in advance. Locker access is during banking hours after signing the access register.",
        "qas": [
            ("What is the annual medium-locker rent in a metro branch?", "A medium locker in a metro branch costs Rs. 6,000 per year plus GST."),
            ("When is locker rent payable?", "The annual locker rent of Rs. 6,000 plus GST is payable in advance."),
            ("When can customers access a branch locker?", "Locker access is available during banking hours after signing the access register."),
        ],
        "false_fact": "A medium metro locker costs Rs. 4,000 and is payable monthly.",
    },
    {
        "domain": "DOWNLOAD", "product": "Social Security Schemes", "subproduct": "Atal Pension Yojana",
        "doc": "SSS_APY_Product_Note_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: SSS_APY_Product_Note_FY27.pdf | Eligibility] Indian citizens aged 18 to 40 with a savings account may enrol, subject to current eligibility rules. The guaranteed pension ranges from Rs. 1,000 to Rs. 5,000 per month from age 60.",
        "qas": [
            ("What is the age range for joining APY?", "Eligible Indian citizens may join APY between ages 18 and 40."),
            ("When does the APY pension begin?", "The guaranteed APY monthly pension begins at age 60."),
            ("What monthly pension amount does APY provide?", "The APY guaranteed pension ranges from Rs. 1,000 to Rs. 5,000 per month from age 60."),
        ],
        "false_fact": "People up to age 50 can join and receive pension from age 55.",
    },
    {
        "domain": "HR", "product": "HR", "subproduct": "Payroll Bank Details",
        "doc": "HR_HRMS_User_Guide_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: HR_HRMS_User_Guide_FY27.pdf | Payroll Bank Details] Update salary-credit bank details in HRMS > My Profile > Bank Details, enter the new Axis Bank account and upload a cancelled cheque. Changes after the 20th take effect in the next payroll cycle.",
        "qas": [
            ("Where do I change the salary-credit account in HRMS?", "Open HRMS > My Profile > Bank Details and enter the new Axis Bank account."),
            ("What proof should I upload for a new salary account?", "Upload a cancelled cheque for the new Axis Bank account in HRMS."),
            ("When do changes submitted after the 20th take effect?", "Changes submitted after the 20th take effect from the next payroll cycle."),
        ],
        "false_fact": "Changes submitted after the 10th apply in the same payroll cycle.",
    },
    {
        "domain": "HR", "product": "HR", "subproduct": "Group Mediclaim",
        "doc": "HR_Mediclaim_GMC_Policy_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: HR_Mediclaim_GMC_Policy_FY27.pdf | Coverage] Base cover includes the employee, spouse and up to 2 dependent children. Parents and parents-in-law can be added under optional Parental Cover with salary-deducted premium during the April enrolment window.",
        "qas": [
            ("Who is covered under the base group mediclaim policy?", "Base cover includes the employee, spouse and up to 2 dependent children."),
            ("Can I add my parents to group mediclaim?", "Parents can be added under optional Parental Cover with a salary-deducted premium."),
            ("When can I enrol parents under the optional cover?", "The optional parental-cover enrolment window is in April."),
        ],
        "false_fact": "Parents are automatically included at no extra premium for 12 months.",
    },
    {
        "domain": "DOWNLOAD", "product": "Operations", "subproduct": "Payments - RTGS",
        "doc": "Ops_Payments_RTGS_SOP_FY27.pdf", "use_case": "Generic RAG",
        "context": "[Doc: Ops_Payments_RTGS_SOP_FY27.pdf | Limits and Cut-off] RTGS minimum is Rs. 2,00,000 and there is no upper ceiling. Branch physical requests are accepted until 4:30 PM on working days.",
        "qas": [
            ("What is the minimum amount for RTGS?", "The RTGS minimum transaction amount is Rs. 2,00,000."),
            ("Is there an upper limit for an RTGS transfer?", "There is no upper ceiling for RTGS transfers; the minimum is Rs. 2,00,000."),
            ("What is the branch cut-off for physical RTGS requests?", "Physical RTGS requests are accepted at branches until 4:30 PM on working days."),
        ],
        "false_fact": "RTGS starts at Rs. 50,000 and the branch cut-off is 6:00 PM.",
    },
    {
        "domain": "DOWNLOAD", "product": "CASA", "subproduct": "Cheque Book Charges",
        "doc": "CASA_Service_Charges_Schedule_FY27.pdf", "use_case": "FAQ",
        "context": "[Doc: CASA_Service_Charges_Schedule_FY27.pdf | Cheque Book] The first 25 cheque leaves per financial year are free on savings accounts. Additional leaves cost Rs. 2.50 each plus GST. Burgundy and Priority customers receive unlimited free leaves.",
        "qas": [
            ("How many cheque leaves are free each financial year?", "The first 25 cheque leaves per financial year are free on a savings account."),
            ("What does each additional cheque leaf cost?", "Each cheque leaf after the first 25 costs Rs. 2.50 plus GST."),
            ("Do Burgundy customers receive free cheque leaves?", "Yes. Burgundy customers receive unlimited free cheque leaves."),
        ],
        "false_fact": "Only 10 cheque leaves are free and every later leaf costs Rs. 5 plus GST.",
    },
]

QUERY_PREFIXES = [
    "{query}",
    "Please clarify: {query}",
    "I need guidance on this: {query}",
    "Could you confirm: {query}",
    "For my situation, {query}",
]
BAD_OFF_TOPIC = "To apply for annual leave, open HRMS > Leave > Apply Leave and submit the dates to your manager."
RUDE_PREFIX = "Obviously, you should know this already. "
RUDE_SUFFIX = " This is a basic question; do not waste the helpdesk's time."


def _session_length(topic_index: int, variant: int) -> int:
    # Ten topics use 2,2,3,3,3; ten use 2,2,2,3,3: 250 turns total.
    if topic_index < 10:
        return (2, 2, 3, 3, 3)[variant]
    return (2, 2, 2, 3, 3)[variant]


def _query_text(template: str, variant: int, variables: dict[str, str]) -> str:
    query = template.format(**variables)
    return QUERY_PREFIXES[variant].format(query=query[0].lower() + query[1:]) if variant else query


def _change_first_number(text: str, fallback_claim: str) -> tuple[str, bool]:
    match = re.search(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?", text)
    if not match:
        return f"{text} {fallback_claim}", False
    value = int(match.group(0).replace(",", ""))
    changed = f"{value + 1:,}" if "," in match.group(0) else str(value + 1)
    return text[:match.start()] + changed + text[match.end():], True


def _domain_name(value: str) -> str:
    return value.replace("_", " ").title()


def _build_rows() -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    rows: list[dict[str, str]] = []
    gold_rows: list[dict[str, object]] = []
    session_number = 0
    row_number = 0

    for session_index in range(100):
        topic_index = session_index % len(TOPICS)
        topic = TOPICS[topic_index]
        variant = session_index // len(TOPICS)
        session_number += 1
        session_id = f"SYN-{session_number:04d}"
        session_turns = 2 if session_index < 50 else 3
        variables = {"reference": f"SR-{session_number:06d}"}
        history: list[dict[str, str]] = []

        for turn_index in range(session_turns):
                query_template, good_answer_template = topic["qas"][turn_index]
                query = _query_text(query_template, variant, variables)
                good_answer = good_answer_template.format(**variables)
                context = topic["context"].format(**variables)
                source_name = topic["doc"].format(**variables)
                mode = row_number % 25
                response = good_answer
                scenario = "correct_faithful"
                sme_correct = "Yes"
                correction = ""
                comment = "Correct"
                labels = (1, 1, 1, 0, 1, None)

                if mode == 0:
                    response = f"{good_answer} {topic['false_fact'].format(**variables)}"
                    scenario = "unsupported_added_claim"
                    sme_correct = "No"
                    correction = good_answer
                    comment = "Incorrect - includes an unsupported claim"
                    labels = (0, 1, 1, 0, 1, 0.5)
                elif mode == 1:
                    response, numeric_contradiction = _change_first_number(
                        good_answer, topic["false_fact"].format(**variables)
                    )
                    scenario = "contradicted_key_number" if numeric_contradiction else "unsupported_added_claim"
                    sme_correct = "No"
                    correction = good_answer
                    comment = (
                        "Incorrect - key figure differs from reference"
                        if numeric_contradiction else "Incorrect - includes an unsupported claim"
                    )
                    labels = (0, 1, 1, 0, 1, 0.0 if numeric_contradiction else 0.5)
                elif mode == 2:
                    response = BAD_OFF_TOPIC
                    scenario = "off_topic_answer"
                    sme_correct = "No"
                    correction = good_answer
                    comment = "Incorrect - answer is off topic"
                    labels = (0, 0, 1, 0, 1, 0.0)
                elif mode == 3:
                    response = f"{RUDE_PREFIX}{good_answer}{RUDE_SUFFIX}"
                    scenario = "rude_tone_correct_facts"
                    sme_correct = "No"
                    correction = good_answer
                    comment = "Factually correct - tone is not professional"
                    labels = (1, 1, 1, 1, 0, 1.0)

                row = {
                    "User Query": query,
                    "Response by ADI": response,
                    "Content Retrieved by ADI": context,
                    "Use case Tagged by ADI": topic["use_case"],
                    "Product Tagged by ADI": topic["product"],
                    "Subproduct Tagged by ADI": topic["subproduct"],
                    "Subproduct Tagged by ADI - comment": comment,
                    "Document Name Retrieved by ADI": source_name,
                    "SME Employee ID": f"SME{1021 + (session_number % 7) * 13:04d}",
                    "Is ADI response Correct? (Yes/No)": sme_correct,
                    "If ADI response incorrect(Enter right response)": correction,
                    "Document Name(s) Expected to be Referred": source_name,
                    "Product as per SME": topic["product"],
                    "Subproduct as per SME": topic["subproduct"],
                    "Session ID": session_id,
                    "Session Turn": str(turn_index + 1),
                    "Session Length": str(session_turns),
                    "Prior Conversation (JSON)": json.dumps(history, ensure_ascii=False),
                }
                rows.append(row)
                gold_rows.append({
                    "row_id": row_number,
                    "session_id": session_id,
                    "session_turn": turn_index + 1,
                    "user_query": query,
                    "scenario": scenario,
                    **dict(zip((
                        "gold_faithful",
                        "gold_answer_relevant",
                        "gold_context_relevant",
                        "gold_toxic",
                        "gold_tone_professional",
                        "gold_answer_correctness",
                    ), labels)),
                })
                history.extend([
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": response},
                ])
                row_number += 1

    if session_number != 100 or row_number != 250:
        raise AssertionError(f"Expected 100 sessions / 250 queries; got {session_number} / {row_number}.")
    _validate(rows, gold_rows)
    return rows, gold_rows


def _validate(rows: list[dict[str, str]], gold_rows: list[dict[str, object]]) -> None:
    session_counts: dict[str, int] = {}
    for row in rows:
        session_counts[row["Session ID"]] = session_counts.get(row["Session ID"], 0) + 1
    if len(session_counts) != 100:
        raise AssertionError(f"Expected 100 unique sessions; got {len(session_counts)}.")
    if sorted(session_counts.values()).count(2) != 50 or sorted(session_counts.values()).count(3) != 50:
        raise AssertionError("Expected 50 two-turn sessions and 50 three-turn sessions.")
    if len({row["User Query"] for row in rows}) != len(rows):
        raise AssertionError("Expected every query row to have distinct query text.")
    if len(gold_rows) != len(rows):
        raise AssertionError("Gold rows must align one-to-one with query rows.")
    for row_id, (row, gold) in enumerate(zip(rows, gold_rows)):
        if gold["row_id"] != row_id or gold["session_id"] != row["Session ID"]:
            raise AssertionError(f"Gold/data row alignment failed at row_id {row_id}.")
        needs_gt = row["Is ADI response Correct? (Yes/No)"] == "No"
        if needs_gt != bool(row["If ADI response incorrect(Enter right response)"].strip()):
            raise AssertionError(f"SME correction missing/misapplied at row_id {row_id}.")
        if needs_gt != (gold["gold_answer_correctness"] is not None):
            raise AssertionError(f"Correctness gold should only be populated for SME-No row_id {row_id}.")
        expected_history = [] if int(row["Session Turn"]) == 1 else None
        if expected_history == [] and json.loads(row["Prior Conversation (JSON)"]):
            raise AssertionError(f"First turn must have empty history at row_id {row_id}.")
        if int(row["Session Turn"]) > 1 and not json.loads(row["Prior Conversation (JSON)"]):
            raise AssertionError(f"Follow-up turn must have prior history at row_id {row_id}.")


def main() -> None:
    rows, gold_rows = _build_rows()
    with DATA_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=DATA_COLUMNS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    with GOLD_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=GOLD_COLUMNS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(gold_rows)

    session_counts: dict[str, int] = {}
    for row in rows:
        session_counts[row["Session ID"]] = session_counts.get(row["Session ID"], 0) + 1
    sme_no = sum(row["Is ADI response Correct? (Yes/No)"] == "No" for row in rows)
    modes: dict[str, int] = {}
    for row in gold_rows:
        modes[row["scenario"]] = modes.get(row["scenario"], 0) + 1
    print(f"Wrote {DATA_CSV.name}: {len(session_counts)} sessions, {len(rows)} queries")
    print(f"Session lengths: {sum(n == 2 for n in session_counts.values())} x 2 turns; "
          f"{sum(n == 3 for n in session_counts.values())} x 3 turns")
    print(f"SME Yes: {len(rows) - sme_no}; SME No: {sme_no}")
    print(f"Wrote {GOLD_CSV.name}; scenario counts: {json.dumps(modes, sort_keys=True)}")


if __name__ == "__main__":
    main()
