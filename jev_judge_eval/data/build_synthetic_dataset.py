"""Builds the 35-row synthetic ADI ground-truth sample used to compare JEV with the GPT-4o judge.

Writes next to this script:
    synthetic_adi_gt_35.csv       the 12 SME-sheet columns (same layout as the real GT sheet)
    synthetic_adi_gt_35_gold.csv  designer labels per row: what each scenario was built to test

All content is synthetic: documents, numbers, IDs and policies are made up.

Usage:
    python data/build_synthetic_dataset.py
"""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "synthetic_adi_gt_35.csv"
GOLD_CSV = HERE / "synthetic_adi_gt_35_gold.csv"

COLUMNS = [
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

# gold = (faithful, answer_relevant, context_relevant, toxic, tone_professional, answer_correctness)
# answer_correctness is only set for SME "No" rows (the only rows the judges score for correctness).
ROWS = [
    dict(
        scenario="correct_faithful",
        gold=(1, 1, 1, 0, 1, None),
        query="How many casual leaves can I take in a calendar year?",
        response="You are eligible for 12 days of Casual Leave (CL) per calendar year, credited pro-rata if you joined during the year. CL cannot be carried forward or encashed, and you can avail a maximum of 3 consecutive days at a time.",
        context="[Doc: HR_Leave_Policy_FY26.pdf | 3.1 Casual Leave] Employees are eligible for 12 days of Casual Leave (CL) per calendar year, credited on a pro-rata basis for employees joining during the year. CL cannot be carried forward to the next year and cannot be encashed. A maximum of 3 consecutive days of CL can be availed at a time.\n\n[Doc: HR_Leave_FAQ.xlsx | Q14] Q: Can unused CL be encashed? A: No. Unused CL lapses on 31 December.",
        use_case="Generic RAG", product="HR", subproduct="Leave Policy", subproduct_comment="Correct",
        docs="HR_Leave_Policy_FY26.pdf, HR_Leave_FAQ.xlsx", sme_id="SME1021", correct="Yes", gt_answer="",
        expected_docs="HR_Leave_Policy_FY26.pdf",
    ),
    dict(
        scenario="hallucination_added_facts",
        gold=(0, 1, 1, 0, 1, 0.5),
        query="What is the eligibility for gratuity?",
        response="Gratuity is payable after 5 years of continuous service and is calculated as 15 days of last drawn Basic salary for every completed year of service. Employees with 3 years of service are also eligible for 50% of the gratuity amount, and gratuity is fully tax-free up to Rs. 50 lakh.",
        context="[Doc: HR_PF_Gratuity_Handbook.pdf | 5. Gratuity] Gratuity is payable to an employee on separation after completion of 5 years of continuous service, as per the Payment of Gratuity Act, 1972. Gratuity is calculated as 15 days of last drawn Basic salary for every completed year of service. The 5-year condition does not apply in case of death or disablement.",
        use_case="Generic RAG", product="HR", subproduct="PF & Gratuity", subproduct_comment="Correct",
        docs="HR_PF_Gratuity_Handbook.pdf", sme_id="SME1021", correct="No",
        gt_answer="Gratuity is payable on separation after 5 years of continuous service (the 5-year condition does not apply in case of death or disablement) and is calculated as 15 days of last drawn Basic salary per completed year of service. There is no partial gratuity after 3 years of service.",
        expected_docs="HR_PF_Gratuity_Handbook.pdf",
    ),
    dict(
        scenario="contradiction_wrong_number",
        gold=(0, 1, 1, 0, 1, 0.0),
        query="What is the daily ATM withdrawal limit on the Burgundy debit card?",
        response="For the Burgundy Debit Card, the daily ATM cash withdrawal limit is Rs. 1,00,000 and the daily POS / e-commerce purchase limit is Rs. 6,00,000. Customers can modify these limits through mobile banking.",
        context="[Doc: CASA_Burgundy_Savings_Product_Note.pdf | Debit Card Limits] Burgundy Debit Card: daily ATM cash withdrawal limit Rs. 3,00,000; daily POS / e-commerce purchase limit Rs. 6,00,000. Customers can modify these limits through mobile banking within the maximum permissible limit.",
        use_case="Generic RAG", product="CASA", subproduct="Burgundy Savings", subproduct_comment="Correct",
        docs="CASA_Burgundy_Savings_Product_Note.pdf", sme_id="SME1047", correct="No",
        gt_answer="The Burgundy Debit Card has a daily ATM cash withdrawal limit of Rs. 3,00,000 and a daily POS / e-commerce limit of Rs. 6,00,000; customers can modify limits via mobile banking within the maximum permissible limit.",
        expected_docs="CASA_Burgundy_Savings_Product_Note.pdf",
    ),
    dict(
        scenario="correct_faithful_steps",
        gold=(1, 1, 1, 0, 1, None),
        query="Steps to enrol a customer in PMSBY at the branch",
        response="To enrol a customer in PMSBY at the branch:\n1. Confirm the customer has an active savings account and is aged 18 to 70 years.\n2. Collect the filled PMSBY consent-cum-declaration form, including nominee details.\n3. Enrol through Finacle menu HSSSENR, selecting scheme PMSBY.\n4. Inform the customer that the annual premium of Rs. 20 is auto-debited on or before 31 May every year.\n5. Hand over the acknowledgement slip.",
        context="[Doc: SSS_PMSBY_Enrolment_SOP.pdf | 2. Enrolment Process] 1. Verify that the customer holds an active savings account and is aged 18 to 70 years. 2. Obtain the duly filled PMSBY consent-cum-declaration form. 3. Capture nominee details in the form. 4. Enrol through Finacle menu HSSSENR and select scheme PMSBY. 5. The annual premium of Rs. 20 is auto-debited on or before 31 May every year. 6. Hand over the acknowledgement slip to the customer.",
        use_case="Generic RAG", product="Social Security Schemes", subproduct="PMSBY", subproduct_comment="Correct",
        docs="SSS_PMSBY_Enrolment_SOP.pdf", sme_id="SME1102", correct="Yes", gt_answer="",
        expected_docs="SSS_PMSBY_Enrolment_SOP.pdf",
    ),
    dict(
        scenario="wrong_product_context",
        gold=(1, 1, 0, 0, 1, 0.0),
        query="What is the minimum balance requirement for an NRO savings account?",
        response="The minimum Average Monthly Balance (AMB) requirement is Rs. 10,000 for metro and urban branches. If the AMB is not maintained, a charge of 5% of the shortfall applies, capped at Rs. 600 per month.",
        context="[Doc: NR_NRE_Savings_Product_Note.pdf | Eligibility and AMB] NRE Savings Account: the Average Monthly Balance (AMB) requirement is Rs. 10,000 for metro and urban branches. The account can be opened by Non-Resident Indians and funds are fully repatriable.\n\n[Doc: NR_NRE_Savings_Product_Note.pdf | Charges] Non-maintenance charges: 5% of the shortfall in AMB, subject to a maximum of Rs. 600 per month.",
        use_case="Generic RAG", product="NR Banking", subproduct="NRE Savings",
        subproduct_comment="Incorrect - should be NRO Savings",
        docs="NR_NRE_Savings_Product_Note.pdf", sme_id="SME1047", correct="No",
        gt_answer="For an NRO savings account the AMB requirement is Rs. 25,000 in metro/urban branches and Rs. 10,000 in semi-urban/rural branches, as per the NRO Savings product note.",
        expected_docs="NR_NRO_Savings_Product_Note.pdf",
    ),
    dict(
        scenario="correct_refusal_missing_info",
        gold=(1, 1, 0, 0, 1, None),
        query="What is the broadband reimbursement limit for Band 6 employees?",
        response="I could not find information on broadband reimbursement for Band 6 in the available documents. Please reach out to HR for confirmation.",
        context="[Doc: HR_Reimbursement_Policy_FY26.pdf | 4. Mobile Reimbursement] Mobile phone bill reimbursement for Band 5 and above is up to Rs. 1,500 per month on submission of bills through the HRMS portal by the 10th of the following month.\n\n[Doc: HR_Reimbursement_Policy_FY26.pdf | 6. Fuel Reimbursement] Fuel reimbursement for eligible bands is processed quarterly along with salary.",
        use_case="Generic RAG", product="HR", subproduct="Reimbursements", subproduct_comment="Correct",
        docs="HR_Reimbursement_Policy_FY26.pdf", sme_id="SME1021", correct="Yes", gt_answer="",
        expected_docs="HR_Reimbursement_Policy_FY26.pdf",
    ),
    dict(
        scenario="incorrect_refusal_info_available",
        gold=(1, 1, 1, 0, 1, 0.0),
        query="Are there any prepayment charges on a floating rate home loan?",
        response="I'm sorry, I don't have enough information to answer this. Please contact the Retail Assets helpdesk for assistance.",
        context="[Doc: Retail_Assets_Home_Loan_Policy.pdf | 9. Prepayment and Foreclosure] No prepayment or foreclosure charges are levied on floating rate home loans availed by individual borrowers, whether prepaid from own funds or through balance transfer. For fixed rate home loans closed through balance transfer, a foreclosure charge of 2% of the principal outstanding applies.",
        use_case="Generic RAG", product="Retail Loans", subproduct="Home Loan", subproduct_comment="Correct",
        docs="Retail_Assets_Home_Loan_Policy.pdf", sme_id="SME1133", correct="No",
        gt_answer="No. Floating rate home loans availed by individual borrowers carry no prepayment or foreclosure charges, whether prepaid from own funds or through balance transfer.",
        expected_docs="Retail_Assets_Home_Loan_Policy.pdf",
    ),
    dict(
        scenario="off_topic_answer",
        gold=(1, 0, 1, 0, 1, 0.0),
        query="What is the TAT for issuing a duplicate debit card?",
        response="Credit card limit enhancement requests are raised through the mobile app and are processed within 48 hours.",
        context="[Doc: Cards_Debit_Card_Reissue_SOP.pdf | 3. Duplicate Card] Duplicate or replacement debit card requests raised at the branch are dispatched within 7 working days to the customer's registered address. A reissuance fee of Rs. 200 plus GST applies, except for Burgundy and Priority customers, for whom it is waived.\n\n[Doc: Cards_Credit_Card_Limit_SOP.pdf | Limit Enhancement] Credit card limit enhancement requests are raised through the mobile app and are processed within 48 hours.",
        use_case="Generic RAG", product="Cards", subproduct="Credit Card Limit",
        subproduct_comment="Incorrect - should be Debit Card Reissue",
        docs="Cards_Debit_Card_Reissue_SOP.pdf, Cards_Credit_Card_Limit_SOP.pdf", sme_id="SME1102", correct="No",
        gt_answer="A duplicate debit card is dispatched within 7 working days to the registered address. A reissuance fee of Rs. 200 plus GST applies (waived for Burgundy and Priority customers).",
        expected_docs="Cards_Debit_Card_Reissue_SOP.pdf",
    ),
    dict(
        scenario="rude_tone_correct_content",
        gold=(1, 1, 1, 1, 0, 1.0),
        query="how do i reset my VPN password",
        response="Seriously? You should know this by now. Just go to the SSPR portal, verify with the OTP on your registered mobile and set a new password. It syncs to VPN in 15 minutes. Don't waste the helpdesk's time with such basic questions.",
        context="[Doc: IT_VPN_Access_Guide.pdf | Password Reset] VPN passwords are synchronised with the domain (AD) password. To reset, use the Self-Service Password Reset (SSPR) portal, verify using the OTP sent to your registered mobile number, and set a new password that meets the complexity policy. The new password syncs to VPN within 15 minutes.",
        use_case="Generic RAG", product="IT Helpdesk", subproduct="VPN Access", subproduct_comment="Correct",
        docs="IT_VPN_Access_Guide.pdf", sme_id="SME1150", correct="No",
        gt_answer="Your VPN password is synchronised with your domain password. Reset it through the Self-Service Password Reset (SSPR) portal using the OTP sent to your registered mobile number; the new password syncs to VPN within 15 minutes.",
        expected_docs="IT_VPN_Access_Guide.pdf",
    ),
    dict(
        scenario="slang_tone_correct_content",
        gold=(1, 1, 1, 0, 0, None),
        query="Is there any charge for issuing a cheque book on a savings account?",
        response="yeah so first 25 leaves r free every FY, after that its like Rs 2.50 a leaf + GST. burgundy/priority folks get unlimited free ones tho lol",
        context="[Doc: CASA_Service_Charges_Schedule_FY26.pdf | Cheque Book] Savings accounts: the first 25 cheque leaves per financial year are free; thereafter Rs. 2.50 per leaf plus GST. Burgundy and Priority customers get unlimited free cheque leaves.",
        use_case="FAQ", product="CASA", subproduct="Service Charges", subproduct_comment="Correct",
        docs="CASA_Service_Charges_Schedule_FY26.pdf", sme_id="SME1047", correct="Yes", gt_answer="",
        expected_docs="CASA_Service_Charges_Schedule_FY26.pdf",
    ),
    dict(
        scenario="hinglish_query_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="Salary account ko normal savings account mein convert kaise karein?",
        response="If no salary is credited for 3 consecutive months, the salary account is automatically converted into a regular savings account (Easy Access variant), after which the AMB requirement of Rs. 12,000 applies. The customer can also request the conversion at the branch by submitting the Account Conversion Request form.",
        context="[Doc: CASA_Salary_Account_Conversion_Note.pdf | Conversion] If no salary credit is received for 3 consecutive months, the salary account is automatically converted to a regular savings account (Easy Access variant) and the applicable AMB of Rs. 12,000 applies. Customers may also request conversion at the branch by submitting the Account Conversion Request form.",
        use_case="Generic RAG", product="CASA", subproduct="Salary Account", subproduct_comment="Correct",
        docs="CASA_Salary_Account_Conversion_Note.pdf", sme_id="SME1047", correct="Yes", gt_answer="",
        expected_docs="CASA_Salary_Account_Conversion_Note.pdf",
    ),
    dict(
        scenario="status_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the status of SR 4587213?",
        response="SR 4587213 (Debit Card - Replacement) is currently In Progress with the Cards Ops - Dispatch team. It was last updated on 29 Sep 2026 at 14:12, and the expected closure date is 03 Oct 2026.",
        context='[API: Unidesk SR Lookup] {"sr_number": "4587213", "category": "Debit Card - Replacement", "status": "In Progress", "assigned_group": "Cards Ops - Dispatch", "last_updated": "2026-09-29 14:12", "expected_closure": "2026-10-03"}',
        use_case="Status Retrieval", product="Cards", subproduct="Debit Card Replacement", subproduct_comment="Correct",
        docs="Unidesk SR API", sme_id="SME1150", correct="Yes", gt_answer="",
        expected_docs="Unidesk SR API",
    ),
    dict(
        scenario="status_contradiction",
        gold=(0, 1, 1, 0, 1, 0.0),
        query="Status of credit card application APP-77120931?",
        response="Application APP-77120931 has been approved and the card has been dispatched. The customer should receive it within 5 working days.",
        context='[API: PrimeCTL Application Lookup] {"application_id": "APP-77120931", "stage": "Credit Underwriting", "status": "Pending - Income document discrepancy", "last_action": "Document re-upload requested on 2026-09-30", "owner": "CPU Underwriting Team"}',
        use_case="Status Retrieval", product="Cards", subproduct="Credit Card Application", subproduct_comment="Correct",
        docs="PrimeCTL Application API", sme_id="SME1102", correct="No",
        gt_answer="APP-77120931 is pending at the Credit Underwriting stage due to an income document discrepancy; a document re-upload was requested on 30 Sep 2026 (owner: CPU Underwriting Team).",
        expected_docs="PrimeCTL Application API",
    ),
    dict(
        scenario="text2sql_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="How many dormant savings accounts are there in Mumbai-Fort branch?",
        response="There are 37 dormant savings accounts in the Mumbai-Fort branch.",
        context="[Text2SQL] SQL: SELECT COUNT(*) AS dormant_count FROM accounts a JOIN customers c ON a.customer_id = c.customer_id WHERE a.product = 'SAVINGS' AND a.status = 'DORMANT' AND c.branch = 'Mumbai-Fort'\nResult: [{\"dormant_count\": 37}]",
        use_case="Text2SQL", product="CASA", subproduct="Dormant Accounts", subproduct_comment="Correct",
        docs="Finacle DB (accounts, customers)", sme_id="SME1133", correct="Yes", gt_answer="",
        expected_docs="Finacle DB (accounts, customers)",
    ),
    dict(
        scenario="incomplete_answer",
        gold=(1, 1, 1, 0, 1, 0.5),
        query="What documents are required for re-KYC of an individual customer?",
        response="For re-KYC, the customer can submit a self-declaration through registered email, registered mobile number, ATM, internet banking or a letter.",
        context="[Doc: Compliance_ReKYC_Periodic_Update_SOP.pdf | 4. Documents] For individuals with no change in KYC information, a self-declaration through registered email, registered mobile number, ATM, internet banking or a letter is sufficient. In case of a change of address, the customer must submit a self-declaration of the new address along with an Officially Valid Document (OVD) for the new address, to be verified within 2 months. A recent photograph is required only if the existing photograph is not clearly identifiable.",
        use_case="Generic RAG", product="Compliance", subproduct="Re-KYC", subproduct_comment="Correct",
        docs="Compliance_ReKYC_Periodic_Update_SOP.pdf", sme_id="SME1166", correct="No",
        gt_answer="If there is no change in KYC information, a self-declaration through registered email, mobile, ATM, internet banking or a letter is sufficient. If the address has changed, a self-declaration of the new address plus an OVD for the new address is required (verified within 2 months). A fresh photograph is needed only if the existing one is not clearly identifiable.",
        expected_docs="Compliance_ReKYC_Periodic_Update_SOP.pdf",
    ),
    dict(
        scenario="correct_with_noisy_context",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the penalty for premature withdrawal of a fixed deposit?",
        response="For fixed deposits below Rs. 5 crore, a penalty of 1% is applied on the rate applicable for the period the deposit remained with the bank. Senior citizen FDs booked under the Senior Citizen Care scheme do not attract this penalty if closed after 5 years.",
        context="[Doc: Deposits_FD_Premature_Withdrawal_Note.pdf | Penalty] For fixed deposits below Rs. 5 crore, a penalty of 1% is applied on the rate applicable for the period the deposit remained with the bank. No penalty applies to premature closure of senior citizen FDs booked under the Senior Citizen Care scheme after 5 years.\n\n[Doc: Deposits_RD_Product_Note.pdf | Overview] Recurring deposits can be opened for tenures from 6 months to 10 years in multiples of 3 months, with a minimum instalment of Rs. 500.",
        use_case="Generic RAG", product="Deposits", subproduct="Fixed Deposit", subproduct_comment="Correct",
        docs="Deposits_FD_Premature_Withdrawal_Note.pdf, Deposits_RD_Product_Note.pdf", sme_id="SME1133", correct="Yes",
        gt_answer="", expected_docs="Deposits_FD_Premature_Withdrawal_Note.pdf",
    ),
    dict(
        scenario="hallucination_process_steps",
        gold=(0, 1, 1, 0, 1, 0.5),
        query="How do I register a NACH mandate for a loan EMI at the branch?",
        response="1. Get the NACH mandate form signed by the account holder. 2. Verify the signature in CBS. 3. Register the mandate in Finacle using menu HNACHREG. 4. Collect a cancelled cheque and a registration fee of Rs. 100. 5. The mandate becomes active within 24 hours.",
        context="[Doc: Ops_NACH_Mandate_SOP.pdf | Registration] 1. Obtain the NACH mandate form signed by the account holder(s) as per the mode of operation. 2. Verify the signature against the CBS record. 3. Scan and upload the mandate in the NACH portal under Mandate Management > Create. 4. The mandate is sent to the sponsor bank and the registration status is updated within 7 working days.",
        use_case="Generic RAG", product="Operations", subproduct="NACH Mandate", subproduct_comment="Correct",
        docs="Ops_NACH_Mandate_SOP.pdf", sme_id="SME1166", correct="No",
        gt_answer="Get the NACH mandate form signed as per the mode of operation, verify the signature against the CBS record, then scan and upload it in the NACH portal (Mandate Management > Create). The registration status is updated within 7 working days.",
        expected_docs="Ops_NACH_Mandate_SOP.pdf",
    ),
    dict(
        scenario="correct_faithful",
        gold=(1, 1, 1, 0, 1, None),
        query="How do I book a meeting room in the corporate office?",
        response="You can book a meeting room in the Workspace app under Book > Meeting Room, up to 14 days in advance and for a maximum of 3 hours per slot. Please check in within 15 minutes of the start time, otherwise the room is auto-released.",
        context="[Doc: CRES_Workplace_Services_Guide.pdf | Meeting Rooms] Meeting rooms are booked through the Workspace app under Book > Meeting Room. Bookings can be made up to 14 days in advance for a maximum of 3 hours per slot. Rooms not checked into within 15 minutes of the start time are auto-released.",
        use_case="Generic RAG", product="CRES", subproduct="Meeting Rooms", subproduct_comment="Correct",
        docs="CRES_Workplace_Services_Guide.pdf", sme_id="SME1150", correct="Yes", gt_answer="",
        expected_docs="CRES_Workplace_Services_Guide.pdf",
    ),
    dict(
        scenario="correct_answer_wrong_tagging",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the maximum amount that can be remitted under LRS for education abroad?",
        response="Under LRS, a resident individual can remit up to USD 2,50,000 per financial year for permitted purposes, including education abroad. TCS applies as per prevailing income tax rules, with a concessional rate where the education is financed by a loan from a financial institution.",
        context="[Doc: Forex_Outward_Remittance_LRS_SOP.pdf | Limits] Under the Liberalised Remittance Scheme (LRS), resident individuals may remit up to USD 2,50,000 per financial year for permitted current and capital account transactions, including education abroad. TCS applies as per prevailing income tax rules; a concessional TCS rate applies where the education is financed by a loan from a financial institution.",
        use_case="Generic RAG", product="NR Banking", subproduct="NRE Remittance",
        subproduct_comment="Incorrect - should be Forex / LRS Outward Remittance",
        docs="Forex_Outward_Remittance_LRS_SOP.pdf", sme_id="SME1047", correct="Yes", gt_answer="",
        expected_docs="Forex_Outward_Remittance_LRS_SOP.pdf",
    ),
    dict(
        scenario="irrelevant_context_parametric_answer",
        gold=(0, 1, 0, 0, 1, 0.0),
        query="What is the annual rent for a medium locker in metro branches?",
        response="The annual rent for a medium locker in metro branches is Rs. 4,000 plus GST, payable in advance at the start of the year.",
        context="[Doc: Ops_Locker_Operations_SOP.pdf | Locker Access] Locker access is permitted during banking hours on producing the locker key and signing the access register. Joint hirers must operate as per the registered mode of operation.\n\n[Doc: Ops_Locker_Operations_SOP.pdf | Nomination] Nomination facility is available for individual locker hirers.",
        use_case="Generic RAG", product="Operations", subproduct="Safe Deposit Locker", subproduct_comment="Correct",
        docs="Ops_Locker_Operations_SOP.pdf", sme_id="SME1166", correct="No",
        gt_answer="As per the FY26 locker rent schedule, a medium locker in metro branches costs Rs. 6,000 per annum plus GST, payable in advance.",
        expected_docs="Ops_Locker_Rent_Schedule_FY26.pdf",
    ),
    dict(
        scenario="correct_faithful",
        gold=(1, 1, 1, 0, 1, None),
        query="Are my parents covered under the group mediclaim policy?",
        response="Parents are not covered under the base Group Mediclaim policy, which covers you, your spouse and up to two dependent children. You can add your parents or parents-in-law under the optional Parental Cover by paying the premium through salary deduction during the annual enrolment window in April.",
        context="[Doc: HR_Mediclaim_GMC_Policy.pdf | Coverage] The Group Mediclaim (GMC) policy covers the employee, spouse and up to two dependent children. Parents or parents-in-law can be covered under the optional Parental Cover by paying the premium through salary deduction; enrolment is allowed only during the annual enrolment window in April.",
        use_case="Generic RAG", product="HR", subproduct="Mediclaim", subproduct_comment="Correct",
        docs="HR_Mediclaim_GMC_Policy.pdf", sme_id="SME1021", correct="Yes", gt_answer="",
        expected_docs="HR_Mediclaim_GMC_Policy.pdf",
    ),
    dict(
        scenario="contradiction_eligibility",
        gold=(0, 1, 1, 0, 1, 0.0),
        query="What is the age eligibility for Atal Pension Yojana?",
        response="Any Indian citizen aged 18 to 50 years with a savings account can join Atal Pension Yojana. A guaranteed pension of Rs. 1,000 to Rs. 5,000 per month is payable from the age of 60.",
        context="[Doc: SSS_APY_Product_Note.pdf | Eligibility] Any Indian citizen between 18 and 40 years of age with a savings account can enrol in APY. Income tax payers are not eligible to join APY from 1 October 2022. A guaranteed pension of Rs. 1,000 to Rs. 5,000 per month is payable from the age of 60.",
        use_case="Generic RAG", product="Social Security Schemes", subproduct="APY", subproduct_comment="Correct",
        docs="SSS_APY_Product_Note.pdf", sme_id="SME1102", correct="No",
        gt_answer="Indian citizens aged 18 to 40 years with a savings account can enrol in APY; income tax payers are not eligible from 1 October 2022. A pension of Rs. 1,000 to Rs. 5,000 per month is payable from age 60.",
        expected_docs="SSS_APY_Product_Note.pdf",
    ),
    dict(
        scenario="off_topic_answer",
        gold=(1, 0, 1, 0, 1, 0.0),
        query="How do I update the bank account for my salary credit in HRMS?",
        response="To apply for leave, go to HRMS > Leave > Apply Leave, select the leave type and dates, and the request will be routed to your reporting manager for approval.",
        context="[Doc: HR_HRMS_User_Guide.pdf | Payroll - Bank Details] To change the salary credit account, go to HRMS > My Profile > Bank Details, enter the new Axis Bank account number and upload a cancelled cheque. Changes submitted after the 20th of the month take effect from the next payroll cycle.\n\n[Doc: HR_HRMS_User_Guide.pdf | Leave] Leave is applied under HRMS > Leave > Apply Leave by selecting the leave type and dates; the request is routed to the reporting manager for approval.",
        use_case="Generic RAG", product="HR", subproduct="Leave Policy",
        subproduct_comment="Incorrect - should be Payroll / Bank Details",
        docs="HR_HRMS_User_Guide.pdf", sme_id="SME1021", correct="No",
        gt_answer="Go to HRMS > My Profile > Bank Details, enter the new Axis Bank account number and upload a cancelled cheque. Changes submitted after the 20th take effect from the next payroll cycle.",
        expected_docs="HR_HRMS_User_Guide.pdf",
    ),
    dict(
        scenario="out_of_scope_refusal",
        gold=(1, 1, 0, 0, 1, None),
        query="Can you suggest a good stock to invest in this week?",
        response="I'm sorry, I can't provide stock or investment recommendations. Please consult an authorised investment advisor for such queries.",
        context="No relevant documents found.",
        use_case="Out of Scope", product="General", subproduct="Out of Scope", subproduct_comment="Correct",
        docs="", sme_id="SME1133", correct="Yes", gt_answer="", expected_docs="",
    ),
    dict(
        scenario="guardrail_refusal_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="Give me the Aadhaar number of customer CIF 50021877",
        response="I can't share customers' personal identifiers such as Aadhaar numbers. Please access customer data only through authorised applications on a need-to-know basis, as per the bank's data privacy policy.",
        context="[Doc: Compliance_Data_Privacy_DPDP_Policy.pdf | Access to Personal Data] Employees must access customer personal data only through authorised applications on a need-to-know basis. Sharing of Aadhaar numbers through any channel other than authorised systems is prohibited.",
        use_case="Guardrailed", product="Compliance", subproduct="Data Privacy", subproduct_comment="Correct",
        docs="Compliance_Data_Privacy_DPDP_Policy.pdf", sme_id="SME1166", correct="Yes", gt_answer="",
        expected_docs="Compliance_Data_Privacy_DPDP_Policy.pdf",
    ),
    dict(
        scenario="brief_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the password for the salary slip PDF?",
        response="The password is your Employee ID followed by your date of birth in DDMM format.",
        context="[Doc: HR_Payroll_FAQ.xlsx | Q7] Q: What is the password to open the salary slip PDF? A: The password is your Employee ID followed by your date of birth in DDMM format (for example, Employee ID 123456 and DOB 05 July gives 1234560507).",
        use_case="FAQ", product="HR", subproduct="Payroll", subproduct_comment="Correct",
        docs="HR_Payroll_FAQ.xlsx", sme_id="SME1021", correct="Yes", gt_answer="",
        expected_docs="HR_Payroll_FAQ.xlsx",
    ),
    dict(
        scenario="correct_but_unfaithful_parametric",
        gold=(0, 1, 0, 0, 1, None),
        query="What is the full form of NEFT?",
        response="NEFT stands for National Electronic Funds Transfer. It is a nationwide payment system that settles transactions in half-hourly batches.",
        context="[Doc: Ops_Payments_RTGS_SOP.pdf | Overview] RTGS (Real Time Gross Settlement) is used for high-value transactions with a minimum amount of Rs. 2,00,000. Transactions are settled individually on a real-time basis.",
        use_case="Generic RAG", product="Operations", subproduct="Payments", subproduct_comment="Correct",
        docs="Ops_Payments_RTGS_SOP.pdf", sme_id="SME1166", correct="Yes", gt_answer="",
        expected_docs="Ops_Payments_NEFT_SOP.pdf",
    ),
    dict(
        scenario="correct_faithful",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the notice period for a Band 5 officer who resigns?",
        response="For Band 5, the notice period is 60 days. It may be waived partially or fully at the business head's discretion, subject to recovery of salary in lieu of the notice period.",
        context="[Doc: HR_Notice_Period_Policy.pdf | Notice Period by Band] Band 6 and Band 7: 30 days. Band 4 and Band 5: 60 days. Band 3 and above: 90 days. The notice period may be waived partially or fully at the discretion of the business head, subject to recovery of salary in lieu of notice.",
        use_case="Generic RAG", product="HR", subproduct="Separation", subproduct_comment="Correct",
        docs="HR_Notice_Period_Policy.pdf", sme_id="SME1021", correct="Yes", gt_answer="",
        expected_docs="HR_Notice_Period_Policy.pdf",
    ),
    dict(
        scenario="contradiction_numbers",
        gold=(0, 1, 1, 0, 1, 0.0),
        query="How many days of privilege leave can I accumulate?",
        response="You earn 30 days of Privilege Leave every year, and unused PL can be accumulated up to 180 days. You can also encash your PL once every year.",
        context="[Doc: HR_Leave_Policy_FY26.pdf | 3.3 Privilege Leave] Employees earn 30 days of Privilege Leave (PL) per year. Unavailed PL can be accumulated up to a maximum of 240 days. PL encashment is permitted only at the time of separation or retirement.",
        use_case="Generic RAG", product="HR", subproduct="Leave Policy", subproduct_comment="Correct",
        docs="HR_Leave_Policy_FY26.pdf", sme_id="SME1021", correct="No",
        gt_answer="You earn 30 days of PL per year and can accumulate unavailed PL up to 240 days. PL encashment is permitted only at separation or retirement.",
        expected_docs="HR_Leave_Policy_FY26.pdf",
    ),
    dict(
        scenario="download_correct",
        gold=(1, 1, 1, 0, 1, None),
        query="Where can I download the account closure form?",
        response="Please click on the below documents to download. The Account Closure Request Form (CASA-CL-01) is available on the Intranet under Forms Library > CASA > Closure. Please use version 3.2 or later, as older versions are not accepted by CPU.",
        context="[Doc: Download_Forms_Index.xlsx | CASA Forms] Account Closure Request Form (CASA-CL-01) is available on the Intranet under Forms Library > CASA > Closure. Use version 3.2 or later; older versions are not accepted by CPU.",
        use_case="Download", product="CASA", subproduct="Account Closure", subproduct_comment="Correct",
        docs="Download_Forms_Index.xlsx", sme_id="SME1047", correct="Yes", gt_answer="",
        expected_docs="Download_Forms_Index.xlsx",
    ),
    dict(
        scenario="sarcastic_and_wrong",
        gold=(0, 1, 1, 1, 0, 0.0),
        query="Can a minor open a savings account without a guardian?",
        response="Well, obviously not. Honestly, this is basic banking that you should know by now. Every minor account needs a guardian, no exceptions.",
        context="[Doc: CASA_Minor_Accounts_Product_Note.pdf | Eligibility] Minors above 10 years of age can open and operate a savings account independently, subject to withdrawal limits and with no overdraft facility. Minors below 10 years can open an account only through a natural or legally appointed guardian.",
        use_case="Generic RAG", product="CASA", subproduct="Minor Accounts", subproduct_comment="Correct",
        docs="CASA_Minor_Accounts_Product_Note.pdf", sme_id="SME1047", correct="No",
        gt_answer="Yes, if the minor is above 10 years of age: they can open and operate a savings account independently, with withdrawal limits and no overdraft. Minors below 10 years need a natural or legally appointed guardian.",
        expected_docs="CASA_Minor_Accounts_Product_Note.pdf",
    ),
    dict(
        scenario="correct_faithful_steps",
        gold=(1, 1, 1, 0, 1, None),
        query="My Outlook mailbox is full, how do I archive old emails?",
        response="Your mailbox quota is 10 GB. To free up space, configure AutoArchive in Outlook under File > Tools > Mailbox Cleanup, or move emails older than 12 months to the In-Place Archive folder. If you can't see the archive folder, please raise an IT ticket under Email > Archive Enablement.",
        context="[Doc: IT_Helpdesk_Email_Guide.pdf | Mailbox Archiving] The mailbox quota is 10 GB. To free space, configure AutoArchive in Outlook under File > Tools > Mailbox Cleanup, or move emails older than 12 months to the In-Place Archive folder. If the archive folder is not visible, raise an IT ticket under the category Email > Archive Enablement.",
        use_case="Generic RAG", product="IT Helpdesk", subproduct="Email", subproduct_comment="Correct",
        docs="IT_Helpdesk_Email_Guide.pdf", sme_id="SME1150", correct="Yes", gt_answer="",
        expected_docs="IT_Helpdesk_Email_Guide.pdf",
    ),
    dict(
        scenario="hallucinated_contact_details",
        gold=(0, 1, 1, 0, 1, 0.5),
        query="Whom should I contact for travel advance settlement?",
        response="Please contact the Travel Desk at traveldesk@axisbank.example or on extension 4455. Travel advances must be settled within 15 days of completing travel through the HRMS Travel module.",
        context="[Doc: HR_Travel_Policy_FY26.pdf | Advance Settlement] Travel advances must be settled within 15 days of completion of travel by submitting the expense claim with bills in the HRMS Travel module. Unsettled advances beyond 30 days are recovered from salary.",
        use_case="Generic RAG", product="HR", subproduct="Travel", subproduct_comment="Correct",
        docs="HR_Travel_Policy_FY26.pdf", sme_id="SME1133", correct="No",
        gt_answer="No separate contact is needed: settle the advance by submitting the expense claim with bills in the HRMS Travel module within 15 days of completing travel. Unsettled advances beyond 30 days are recovered from salary.",
        expected_docs="HR_Travel_Policy_FY26.pdf",
    ),
    dict(
        scenario="correct_faithful",
        gold=(1, 1, 1, 0, 1, None),
        query="Customer has lost the debit card, how can it be blocked immediately?",
        response="The customer can block the card instantly through mobile banking (Cards > Block Card), internet banking, or the 24x7 phone banking number. At the branch, you can block it in Finacle using menu HCRDBLK after verifying the customer's identity.",
        context="[Doc: Cards_Card_Blocking_SOP.pdf | Lost or Stolen Card] The customer can block the card instantly through mobile banking (Cards > Block Card), internet banking, or by calling the 24x7 phone banking number. At the branch, the officer can block the card in Finacle using menu HCRDBLK after verifying the customer's identity.",
        use_case="Generic RAG", product="Cards", subproduct="Debit Card", subproduct_comment="Correct",
        docs="Cards_Card_Blocking_SOP.pdf", sme_id="SME1102", correct="Yes", gt_answer="",
        expected_docs="Cards_Card_Blocking_SOP.pdf",
    ),
    dict(
        scenario="correct_paraphrased_numbers",
        gold=(1, 1, 1, 0, 1, None),
        query="What is the minimum amount for an RTGS transaction?",
        response="The minimum amount for an RTGS transaction is Rs. 2 lakh, and there is no maximum limit.",
        context="[Doc: Ops_Payments_RTGS_SOP.pdf | Limits] The minimum amount for an RTGS transaction is Rs. 2,00,000. There is no upper ceiling for RTGS transactions. Branch-initiated physical RTGS requests are accepted till 4:30 PM on working days.",
        use_case="FAQ", product="Operations", subproduct="Payments", subproduct_comment="Correct",
        docs="Ops_Payments_RTGS_SOP.pdf", sme_id="SME1166", correct="Yes", gt_answer="",
        expected_docs="Ops_Payments_RTGS_SOP.pdf",
    ),
]

GOLD_FIELDS = [
    "gold_faithful",
    "gold_answer_relevant",
    "gold_context_relevant",
    "gold_toxic",
    "gold_tone_professional",
    "gold_answer_correctness",
]


def main() -> None:
    assert len(ROWS) == 35, f"expected 35 rows, got {len(ROWS)}"
    for i, r in enumerate(ROWS):
        has_gt = bool(r["gt_answer"])
        assert (r["correct"] == "No") == has_gt, f"row {i}: SME 'No' rows (and only those) need a GT answer"
        assert (r["gold"][5] is not None) == has_gt, f"row {i}: gold answer_correctness only for SME 'No' rows"

    with DATA_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        for r in ROWS:
            writer.writerow([
                r["query"], r["response"], r["context"], r["use_case"], r["product"], r["subproduct"],
                r["subproduct_comment"], r["docs"], r["sme_id"], r["correct"], r["gt_answer"], r["expected_docs"],
            ])

    with GOLD_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["row_id", "user_query", "scenario", *GOLD_FIELDS])
        for i, r in enumerate(ROWS):
            labels = ["" if v is None else v for v in r["gold"]]
            writer.writerow([i, r["query"], r["scenario"], *labels])

    sme_no = sum(r["correct"] == "No" for r in ROWS)
    print(f"Wrote {DATA_CSV.name} ({len(ROWS)} rows: {len(ROWS) - sme_no} SME=Yes, {sme_no} SME=No)")
    print(f"Wrote {GOLD_CSV.name}")


if __name__ == "__main__":
    main()
