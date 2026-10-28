"""HR corpus — synthetic but realistic employee-policy documents.

Facts are grounded in widely known Indian employment norms (EPF/ESI, gratuity,
maternity benefit, IT declarations, etc.); all bank-specific figures, codes and
owners are synthetic. Content is original prose, not copied from any source.
"""

DOCS = [
# ---------------------------------------------------------------- onboarding
{
 "bubble": "HR",
 "slug": "onboarding_orientation",
 "title": "Employee Onboarding & Orientation",
 "body": """
## Day One Checklist
- Complete joining documentation: PAN, Aadhaar, educational certificates, passport-size photos.
- Receive employee ID card, access badge and workstation allocation.
- Attend the welcome session covering code of conduct, leave policy and security guidelines.
- Complete mandatory e-learnings within 30 days: AML, information security, POSH and data privacy.

## Buddy Programme
Every new joiner is assigned a buddy for the first 90 days. The buddy answers day-to-day
questions, introduces the team and helps with system access requests.

## Induction Curriculum
Week 1 covers bank structure and business units. Week 2 covers role-specific training and
product fundamentals. Week 4 includes a branch visit for non-branch employees.

## Probation
Probation is six months for most grades. Confirmation requires completion of induction
modules, acceptable performance reviews and no open disciplinary proceedings.

Policy code: HR-ONB-2026-01 | Owner: Talent Acquisition team.
"""
},
{
 "bubble": "HR",
 "slug": "remote_work_policy",
 "title": "Remote Work Policy",
 "body": """
## Eligibility
Remote work is available to employees in roles that do not require physical presence.
Eligibility is role-based, not request-based. Customer-facing and vault roles are excluded.

## Hybrid Pattern
Eligible employees may work remotely up to two days per week. Remote days must be planned
with the reporting manager at least one working day in advance and recorded in the attendance tool.

## Equipment and Connectivity
The bank provides a laptop and VPN. Employees must maintain a stable internet connection
(minimum 10 Mbps) and a quiet, secure workspace. Home Wi-Fi must use WPA2 or stronger.

## Information Security on Remote Days
- Client and internal documents must never be printed at home.
- Screen-locking is mandatory when stepping away.
- Video calls involving customer data must use the approved collaboration platform only.

## Performance Expectations
Remote work does not change performance standards. Teams define core collaboration hours
(between 10:00 and 17:30 IST) when availability is expected.

Policy code: HR-RWFH-2026-01 | Owner: HR Business Policy team.
"""
},
{
 "bubble": "HR",
 "slug": "attendance_and_swipe",
 "title": "Attendance & Swipe Guidelines",
 "body": """
## Marking Attendance
Employees must swipe their access card or mark attendance through the mobile attendance app
at the start and end of each working day. Manual corrections need reporting-manager approval.

## Late Arrival
Arrivals after 09:45 IST are recorded as late. Three lates in a calendar month trigger a
discussion with the reporting manager. Lates are not a leave substitute.

## Short Leave
Short leave of up to two hours may be approved by the reporting manager and must be
compensated the same week or adjusted against casual leave.

## Absence Without Intimation
Three consecutive days of absence without intimation is treated as a disciplinary matter
and may be considered as abandonment of employment after due process.

Policy code: HR-ATT-2026-02 | Owner: HR Operations team.
"""
},
{
 "bubble": "HR",
 "slug": "flexible_work_hours",
 "title": "Flexible Work Hours Framework",
 "body": """
## Core Hours
The core collaboration window is 10:00 to 17:30 IST. Employees may flex their start time
between 08:00 and 10:30 IST, provided the full workday is completed.

## Staggering
Teams with heavy branch or market dependency may define staggered shifts. Shift definitions
are approved by the business head and published in the team charter.

## Overtime
Overtime is exceptional and must be pre-approved. Approved overtime is compensated as
compensatory off within 45 days, not as cash, except for grades where overtime pay is statutory.

## Flexibility Requests
Flexible start-time requests need reporting-manager approval and must not impact service
windows, market hours or client commitments.

Policy code: HR-FLEX-2026-01 | Owner: HR Business Policy team.
"""
},
{
 "bubble": "HR",
 "slug": "probation_and_confirmation",
 "title": "Probation & Confirmation",
 "body": """
## Probation Duration
Probation is six months. The talent acquisition team may extend probation by up to three
months in documented cases of skill gaps, subject to HRBP approval.

## Reviews During Probation
A check-in is held at day 30, day 90 and day 150. Each check-in is recorded in the HR system
with agreed action items.

## Confirmation Criteria
- Completion of all mandatory e-learnings and role certifications.
- No open disciplinary or conduct issue.
- At least a "Meets Expectations" rating in the probation review.

## Early Termination
Either party may end employment during probation with notice as per the appointment letter,
normally 15 days or pay in lieu.

Policy code: HR-PROB-2026-01 | Owner: Talent Management team.
"""
},
{
 "bubble": "HR",
 "slug": "background_verification",
 "title": "Background Verification Policy",
 "body": """
## Scope
Background verification applies to all new joiners, temporary staff and vendor personnel
with system access. Verification is completed within 60 days of joining.

## Checks Performed
- Identity and address verification against Officially Valid Documents.
- Education and employment history for the last seven years.
- Criminal and court-record check.
- Credit check for roles with fiduciary or cash-handling responsibilities.

## Adverse Findings
Discrepancies are reviewed by the verification cell and HRBP. Material misrepresentation in
education or employment history may lead to withdrawal of the offer or termination.

## Re-Verification
Employees moving to roles requiring higher clearance undergo re-verification before the
transfer is effective.

Policy code: HR-BGV-2026-01 | Owner: Talent Acquisition team.
"""
},
{
 "bubble": "HR",
 "slug": "employee_referral_program",
 "title": "Employee Referral Programme",
 "body": """
## Eligibility
All permanent employees except HR recruiters and the hiring manager for the specific role
may refer candidates. Referrals must be registered in the referral portal before application.

## Reward Structure
Referral rewards are paid in two instalments: 50 percent on joining and 50 percent after
the referred employee completes six months. Senior and niche roles carry higher rewards as
published in the quarterly referral bulletin.

## Clawback
Rewards are clawed back if the referred employee exits within six months or if the referral
is found to violate the anti-nepotism policy.

## Referral Process
1. Register the candidate in the referral portal.
2. Candidate is tagged to the employee for 180 days.
3. On selection, the referral bonus is processed automatically.

Policy code: HR-REF-2026-01 | Owner: Talent Acquisition team.
"""
},
{
 "bubble": "HR",
 "slug": "internal_mobility",
 "title": "Internal Job Mobility",
 "body": """
## Eligibility
Employees may apply for internal openings after 18 months in the current role. Cross-entity
moves are also subject to approval from the current business head.

## Process
1. Apply through the internal career portal.
2. The hiring manager evaluates the profile without prior approval from the current manager.
3. Current manager approval is sought only at the offer stage.

## Notice to Current Team
Internal moves carry a handover period of 30 to 45 days, based on role criticality, agreed
between the two managers.

## Compensation on Move
Lateral moves do not change grade. Promotional moves follow the promotion guidelines.

Policy code: HR-MOB-2026-01 | Owner: Talent Management team.
"""
},
{
 "bubble": "HR",
 "slug": "relocation_policy",
 "title": "Relocation Policy",
 "body": """
## Scope
Relocation support applies to employees moving to a new city on account of a bank-initiated
transfer. Voluntary relocations are not covered.

## Reimbursement Heads
- Movement of household goods up to the approved weight limit by grade.
- Travel for self and dependants.
- Temporary accommodation for up to 14 days.
- Incidentals as a fixed lump sum by grade.

## Process
Submit the transfer order, quotation from an approved mover, and travel proof within 30
days of moving. Reimbursement is processed in the next payroll cycle after approval.

## Recovery Clause
If the employee resigns within 12 months of a bank-funded relocation, the relocation
amount is recoverable on a pro-rata basis.

Policy code: HR-REL-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "domestic_travel_policy",
 "title": "Domestic Travel Policy",
 "body": """
## Booking Rules
- Flights: economy class for grades M1-M3, business class only for M4 and above with
  business-head approval.
- Trains: AC two-tier or equivalent.
- Cabs: app-based or approved vendor with bills.

## Travel Request
Travel must be approved in the travel portal before booking. International and emergency
travel have separate workflows.

## Per Diem
Daily allowance covers meals and local conveyance. Actual hotel bills are reimbursed
separately up to city-wise caps published in the travel annexure.

## Expense Submission
Submit expense claims within 15 days of return. Unsubmitted travel advances are recovered
from the next salary.

Policy code: HR-TRVL-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "international_travel_policy",
 "title": "International Travel Policy",
 "body": """
## Approval
International travel requires business-head and functional CFO approval at least 14 days
in advance. Travel to sanctioned or restricted destinations is prohibited.

## Insurance and Support
The bank provides travel insurance covering medical emergencies, trip cancellation and
baggage loss. Employees must register travel dates with the corporate travel desk.

## Passport and Visa
Passport validity must exceed six months from the return date. Visa costs are reimbursed
for bank-approved travel only.

## Safety Protocol
Employees must save the corporate security helpline, avoid unapproved areas, and report
any security incident to the travel desk within 24 hours.

Policy code: HR-TRVL-I-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "travel_advance_policy",
 "title": "Travel Advance Policy",
 "body": """
## Eligibility
Travel advance is issued for approved travel of five days or more. The advance covers
estimated stay, local conveyance and per diem.

## Advance Limits
Advances are capped at 80 percent of the estimated trip cost. Cash withdrawal of the
advance is capped as per the expense policy.

## Settlement
Settlement must be completed within 15 days of return. Unsettled advances are recovered
from the next payroll and flagged to the manager.

## Multiple Trips
Employees with an outstanding unsettled advance cannot raise a new advance unless the
pending amount is under INR 5,000.

Policy code: HR-TRVL-A-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "accommodation_norms",
 "title": "Hotel & Accommodation Norms",
 "body": """
## City-wise Caps
Metro cities: INR 8,000 per night. Tier-1 cities: INR 6,000 per night. Other cities:
INR 4,500 per night. Caps include taxes.

## Booking Preference
Accommodation must be booked through the approved corporate travel platform. Direct
bookings are reimbursed only with prior approval and valid justification.

## Shared Stay
Employees travelling together may share rooms for internal meetings. Room-sharing norms
apply only with mutual consent and are never mandatory.

## Invoice Requirements
Submit a GST invoice in the employee's name along with the stay dates. Payments to
unregistered properties are not reimbursable.

Policy code: HR-TRVL-H-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "meal_and_incidental_allowance",
 "title": "Meal & Incidental Allowance",
 "body": """
## Daily Allowance
Meal and incidental allowance is paid as a fixed per diem based on travel city category:
Metro INR 1,200, Tier-1 INR 1,000, others INR 800 per day.

## Coverage
The per diem covers meals, local conveyance within the destination city and personal
incidentals. It does not cover alcohol, personal shopping or entertainment.

## Half-day Rule
A travel day spanning more than 8 hours qualifies for full per diem. Days with 4-8 hours
qualify for half per diem.

## Payment
Per diem is paid with the expense settlement, not in advance, unless included in an
approved travel advance.

Policy code: HR-TRVL-M-2026-01 | Owner: Employee Services team.
"""
},
{
 "bubble": "HR",
 "slug": "grade_structure",
 "title": "Grade & Band Structure",
 "body": """
## Band Framework
Grades M1-M7 define individual contributor and managerial levels. Each band has a defined
salary range, role cluster and expected scope.

## Band Movement
Band movement is by promotion or regrading only. Regrading changes the band of a role, not
the employee's performance-based progression.

## Role Clusters
- Individual contributor (M1-M3): execution and subject-matter expertise.
- People manager (M4-M5): team delivery and development.
- Leadership (M6-M7): business-unit and function ownership.

## Salary Range Governance
Offers and increments must stay within band ranges. Exceptions need HRBP and business-head
approval with documented market rationale.

Policy code: HR-GRADE-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "compensation_review",
 "title": "Compensation Review Cycle",
 "body": """
## Annual Cycle
Compensation review is effective 1 April. Rating inputs from the appraisal close in March
feed the increment matrix published by the Rewards team.

## Market Benchmarking
Every role is benchmarked against the banking sector median using annual market surveys.
Positions below the 25th percentile are prioritised for corrections.

## Increment Drivers
Increment is driven by performance rating, position-in-range and business affordability.
The matrix is approved by the compensation committee.

## Communication
Revised compensation letters are released in June. Any query must be raised through the
HR service portal within 30 days of release.

Policy code: HR-COMP-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "annual_increment_cycle",
 "title": "Annual Increment Cycle",
 "body": """
## Timing
The increment cycle runs from April to June. Performance inputs close in March, calibration
in April, and letters are issued in June.

## Eligibility
Employees who joined on or before 31 December of the previous financial year and are not
under a performance improvement plan are eligible.

## Calibration
Ratings are calibrated at business-unit level before increments are computed. Calibration
adjusts rating distribution, never individual compensation directly.

## Promotion During Cycle
Employees promoted in the same cycle receive the higher of the promotion increment or the
annual increment, not both.

Policy code: HR-COMP-I-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "variable_pay_policy",
 "title": "Variable Pay Policy",
 "body": """
## Eligibility
Variable pay applies to grades M3 and above. It is paid annually against business, unit
and individual scorecard achievement.

## Payout Formula
Payout = target variable × business multiplier × unit multiplier × individual multiplier.
Multipliers range from 0 to 1.5 as per the approved scorecard.

## Timing
Variable pay for a financial year is paid in June of the following year. Employees who
resign before the payout date are not eligible unless the separation policy states otherwise.

## Disputes
Scorecard disputes must be raised within 30 days of scorecard communication to the
business review committee.

Policy code: HR-COMP-V-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "joining_and_retention_bonus",
 "title": "Joining & Retention Bonus",
 "body": """
## Joining Bonus
Joining bonuses are limited to niche skills and candidate-negotiated cases approved by the
business head and Rewards. Payment is with the first payroll.

## Retention Bonus
Retention bonuses are paid in milestone tranches against a written retention agreement
approved by the business head and HR.

## Recovery
Joining bonuses are recovered in full if the employee leaves within 12 months. Retention
bonuses are recovered pro-rata for the unserved period of the agreement.

## Documentation
Every bonus must have a signed agreement recording amount, conditions and recovery terms.

Policy code: HR-COMP-B-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "esop_espp",
 "title": "Employee Stock Plans Overview",
 "body": """
## ESOP Programme
Eligible employees receive stock options under the employee stock option scheme approved
by the board. Options vest over a defined schedule and are exercisable per the scheme rules.

## Vesting Schedule
Standard vesting is 25 percent per year over four years from the grant date. Accelerated
vesting requires board committee approval.

## Exercise
Vested options may be exercised during open windows. Trading during closed windows is
prohibited under the insider trading policy.

## Tax Treatment
Perquisite value of options is taxed as per prevailing income-tax rules at exercise.
Employees should consult the tax helpdesk for declarations.

Policy code: HR-ESOP-2026-01 | Owner: Rewards team.
"""
},
{
 "bubble": "HR",
 "slug": "payroll_calendar",
 "title": "Payroll Calendar",
 "body": """
## Payroll Date
Salary is credited on the last working day of each month. If that day is a holiday, credit
happens on the previous working day.

## Input Cut-off
All inputs — attendance, leaves, reimbursements, tax declarations — must be submitted by
the 20th of the month. Inputs after the cut-off are processed in the next cycle.

## Payslip
Payslips are published on the HR self-service portal by the 1st of the following month.
Employees can download payslips for the last five years.

## Payroll Corrections
Errors must be reported within 10 days of credit. Approved corrections are adjusted in
the next payroll cycle.

Policy code: HR-PAY-2026-01 | Owner: Payroll team.
"""
},
{
 "bubble": "HR",
 "slug": "salary_advance_policy",
 "title": "Salary Advance Policy",
 "body": """
## Eligibility
Salary advance is available for genuine emergencies after six months of service. Maximum
advance is one month's net salary.

## Repayment
The advance is recovered over three payrolls by default, or a shorter period agreed in
writing. Recovery cannot reduce take-home below statutory minimums.

## Approval
Advances require reporting-manager and HRBP approval. A second advance is not sanctioned
while a previous one is outstanding.

## Documentation
Supporting documentation of the emergency is required for advances above 50 percent of
net salary.

Policy code: HR-PAY-A-2026-01 | Owner: Payroll team.
"""
},
{
 "bubble": "HR",
 "slug": "tax_declaration_process",
 "title": "Income-Tax Declaration Process",
 "body": """
## Declaration Window
Employees declare proposed investments and rent in April-May each financial year.
Declarations drive monthly tax deduction at source (TDS).

## Eligible Heads
- Section 80C: ELSS, PPF, EPF, life insurance, principal on home loan, tuition fees.
- Section 80D: medical insurance premiums.
- House rent allowance exemption under Section 10(13A).
- Home loan interest under Section 24(b).

## Proof Submission
Investment proofs must be uploaded by the first week of January. Shortfalls in proof
lead to tax recovery in February and March payrolls.

## Form 16
Form 16 is issued by 15 June. Part B includes employer-provided details; Part A carries
the TDS certificate.

Policy code: HR-TAX-2026-01 | Owner: Payroll team.
"""
},
{
 "bubble": "HR",
 "slug": "medical_insurance_cover",
 "title": "Group Medical Insurance Cover",
 "body": """
## Coverage
The group medical policy covers the employee, spouse, up to two dependent children and
dependent parents. Sum insured is defined by grade in the annual benefit summary.

## Inclusions
Hospitalisation, pre and post-hospitalisation expenses, daycare procedures, and
ambulance charges. Maternity is covered for eligible dependants as per policy terms.

## Cashless and Reimbursement
Cashless treatment is available at network hospitals on presentation of the health card.
Reimbursement claims follow the insurer's claim process.

## Addition of Dependants
New dependants must be added within 30 days of the life event (marriage, birth) through
the benefits portal with documentary proof.

Policy code: HR-BEN-M-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "group_term_life_cover",
 "title": "Group Term Life Cover",
 "body": """
## Coverage
Group term life cover is provided at a multiple of annual fixed compensation as per grade.
Coverage is active from the date of joining.

## Nomination
Employees must nominate beneficiaries within 30 days of joining and review nominations
after any life event.

## Claim Process
In the event of a claim, the family contacts the HR benefits helpdesk with the death
certificate and nominee details. The insurer settles the claim as per policy terms.

## Portability
On separation, employees may convert the group cover to an individual policy within the
insurer's conversion window.

Policy code: HR-BEN-L-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "group_personal_accident",
 "title": "Group Personal Accident Cover",
 "body": """
## Coverage
Accidental death and permanent disability are covered up to the sum insured defined by
grade. Temporary total disability is covered as per policy schedule.

## Scope
Coverage applies on and off duty, worldwide, subject to policy exclusions such as
self-inflicted injury and adventure sports without approval.

## Claim Intimation
Claims must be intimated within 30 days of the accident through the benefits portal with
FIR/medical records as applicable.

## Renewal
The policy renews annually. The annual benefit summary publishes the current sum insured.

Policy code: HR-BEN-A-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "wellness_programme",
 "title": "Employee Wellness Programme",
 "body": """
## Pillars
The programme covers physical wellness, mental wellbeing and financial wellness.

## Mental Wellbeing
Confidential counselling sessions are available through the employee assistance provider.
Up to 12 sessions per year per employee and dependants at no cost.

## Physical Wellness
Subsidised health check-ups once a year for employees above 35. Fitness reimbursements
are offered for approved gym or sport memberships up to the annual cap.

## Financial Wellness
Quarterly webinars on taxation, retirement planning and debt management. One-on-one
sessions are bookable through the wellness portal.

Policy code: HR-WELL-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "employee_assistance_program",
 "title": "Employee Assistance Programme (EAP)",
 "body": """
## Confidentiality
EAP counselling is confidential. The provider does not share individual session details
with the bank. Only aggregate utilisation data is shared.

## Access
Employees and dependants can book sessions 24/7 through the EAP app or toll-free line.
Sessions are available in English, Hindi and regional languages.

## Scope
Counselling covers work stress, relationships, anxiety, grief, financial stress and
legal guidance (first consultation).

## Crisis Support
A dedicated crisis line is available for urgent situations with immediate triage.

Policy code: HR-WELL-E-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "learning_and_development",
 "title": "Learning & Development Framework",
 "body": """
## Mandatory Learning
All employees complete annual compliance e-learnings: AML, information security, POSH,
data privacy and code of conduct, by 30 September.

## Learning Hours
Employees are encouraged to complete at least 40 hours of structured learning per year.
Learning hours are tracked on the LXP platform.

## Role Academies
Role academies offer certification paths for credit, operations, treasury, technology and
risk roles. Academy completion feeds the promotion readiness criteria.

## External Programmes
External certifications and executive programmes are reimbursed under the certification
reimbursement policy.

Policy code: HR-LND-2026-01 | Owner: Learning & Development team.
"""
},
{
 "bubble": "HR",
 "slug": "certification_reimbursement",
 "title": "Certification Reimbursement Policy",
 "body": """
## Approved List
Reimbursement applies to certifications on the approved list published annually, such as
CAIIB, CFA, FRM, cloud certifications and role-specific technical certifications.

## Reimbursement Amount
Up to 100 percent of exam fees for certifications on the approved list, capped per grade.
Renewal and membership fees are reimbursed for active certifications.

## Conditions
- Certification must be passed, not merely attempted.
- Employee must be in service on the date of the claim.
- Reimbursement is paid against the fee receipt only.

## Bond
For certifications above the cap threshold, a service commitment of 12 months applies.
Early exit triggers pro-rata recovery.

Policy code: HR-LND-C-2026-01 | Owner: Learning & Development team.
"""
},
{
 "bubble": "HR",
 "slug": "higher_education_policy",
 "title": "Higher Education & Study Leave",
 "body": """
## Study Leave
Study leave of up to 15 days per exam attempt is available for approved professional
examinations. Additional days require business-head approval.

## Sabbatical for Education
Employees with five years of service may apply for an unpaid sabbatical of up to 12 months
for full-time higher education.

## Sponsorship
Full sponsorship is rare and reserved for identified leadership pipelines. Sponsorship
requires a three-year service bond post-completion.

## Return Commitment
Employees returning from study sabbatical are placed in a role at the same grade, subject
to availability and business needs.

Policy code: HR-LND-H-2026-01 | Owner: Learning & Development team.
"""
},
{
 "bubble": "HR",
 "slug": "sabbatical_policy",
 "title": "Sabbatical Policy",
 "body": """
## Purpose
Sabbaticals support long-term personal priorities: higher education, caregiving or
extended travel.

## Eligibility
Employees with five years of continuous service and a consistent "Meets Expectations"
record may apply. Duration is 3 to 12 months.

## Terms
Sabbaticals are unpaid. Group insurance continues during the sabbatical. Seniority and
leave accrual continue but no salary is paid.

## Application and Approval
Applications require a six-month notice, manager endorsement, HRBP approval and business
head sign-off. Approval is discretionary, not an entitlement.

## Rejoining
Employees rejoin at the same grade in an available role. The bank does not guarantee the
same role or team.

Policy code: HR-SAB-2026-01 | Owner: Talent Management team.
"""
},
{
 "bubble": "HR",
 "slug": "promotion_guidelines",
 "title": "Promotion Guidelines",
 "body": """
## Criteria
Promotion requires sustained performance at or above "Exceeds Expectations" for two
consecutive cycles, role readiness and a vacancy or business case at the higher grade.

## Readiness Assessments
For people-manager moves, a manager-readiness assessment and structured panel interview
are mandatory.

## Timing
Promotions are effective 1 April or 1 October. Off-cycle promotions are rare and require
CHRO approval.

## Communication
Promotion decisions are communicated by the manager with HR support. Unsuccessful
candidates receive structured feedback.

Policy code: HR-PROM-2026-01 | Owner: Talent Management team.
"""
},
{
 "bubble": "HR",
 "slug": "lateral_moves_policy",
 "title": "Lateral Moves Policy",
 "body": """
## Definition
A lateral move is a same-grade change of role, team or location. Lateral moves do not
carry a compensation change.

## Eligibility
Employees may seek a lateral move after 18 months in role. Under 18 months, moves need
business-head approval.

## Application
Employees apply to open roles through the internal portal. The current manager is
informed once the employee reaches the interview stage.

## Handover
A handover of 30 days is standard. For critical roles, managers may agree up to 45 days.

Policy code: HR-MOB-L-2026-01 | Owner: Talent Management team.
"""
},
{
 "bubble": "HR",
 "slug": "grievance_redressal",
 "title": "Grievance Redressal Policy",
 "body": """
## Definition
A grievance is any work-related dissatisfaction regarding conditions, treatment or
application of policy.

## Levels
1. Raise with the reporting manager within 15 days of the event.
2. Escalate to HRBP if unresolved in 10 working days.
3. Escalate to the grievance committee for a formal review.

## Timelines
The grievance committee resolves matters within 30 days of formal escalation. The
employee is informed in writing of the outcome.

## Protection
Raising a grievance in good faith does not attract any adverse consequence. Retaliation
is a violation of the code of conduct.

Policy code: HR-GRV-2026-01 | Owner: Employee Relations team.
"""
},
{
 "bubble": "HR",
 "slug": "posh_policy",
 "title": "Prevention of Sexual Harassment (POSH) Policy",
 "body": """
## Commitment
The bank has zero tolerance for sexual harassment at the workplace, in line with the
Sexual Harassment of Women at Workplace Act, 2013.

## Coverage
The policy covers all employees, trainees, contract staff and third parties at any
workplace, including remote work, travel and official events.

## Internal Committee (IC)
Each region has an Internal Committee with a presiding officer and at least half women
members. The committee handles complaints with confidentiality and timelines prescribed
by the Act.

## Complaint Process
Complaints may be filed in writing, by email to the IC or through the grievance portal
within three months of the incident (extendable by three months with reasons).

## Redressal
The IC completes inquiry within 90 days and recommends action. Both parties can appeal to
the appellate authority.

Policy code: HR-POSH-2026-01 | Owner: Employee Relations team.
"""
},
{
 "bubble": "HR",
 "slug": "code_of_conduct",
 "title": "Code of Conduct",
 "body": """
## Core Principles
- Act with integrity in all dealings.
- Treat customers, colleagues and partners with respect.
- Protect confidential information and customer data.
- Avoid conflicts of interest; declare them promptly.

## Conflict of Interest
Employees must disclose outside business interests, family relationships with vendors,
and board positions in other entities through the declaration portal annually.

## Reporting Misconduct
Misconduct may be reported to the manager, HR, compliance or the whistleblower channel.
Good-faith reports are protected.

## Consequences
Violations lead to disciplinary action up to and including termination, and may be
reported to regulators where applicable.

Policy code: HR-CC-2026-01 | Owner: Employee Relations team.
"""
},
{
 "bubble": "HR",
 "slug": "social_media_policy",
 "title": "Social Media Policy",
 "body": """
## Personal Use
Employees may use social media personally but must not imply they speak for the bank.
Branded communications require marketing approval.

## Confidentiality
Do not share customer information, internal data, strategy, or unreleased products.
Confidentiality obligations survive employment.

## Identifying Affiliations
If discussing industry topics where the employee's employment is relevant, the
affiliation must be disclosed or avoided.

## Violations
Breaches that damage the bank's reputation or disclose confidential information are
treated as code-of-conduct violations.

Policy code: HR-SM-2026-01 | Owner: Corporate Communications team.
"""
},
{
 "bubble": "HR",
 "slug": "gifts_and_entertainment",
 "title": "Gifts & Entertainment Policy",
 "body": """
## General Rule
Employees must not accept gifts or entertainment that could influence, or appear to
influence, a business decision.

## Permitted Items
Non-cash promotional items of nominal value (up to INR 2,500) may be accepted if
unsolicited. Anything above must be reported and surrendered or donated.

## Prohibited
Cash, cash equivalents, loans, travel, and entertainment from vendors or customers in an
active selection process are prohibited.

## Declaration
Gifts above the threshold must be declared in the register within five working days.

Policy code: HR-GE-2026-01 | Owner: Compliance team.
"""
},
{
 "bubble": "HR",
 "slug": "exit_process",
 "title": "Exit Process",
 "body": """
## Resignation
Resignation must be submitted in the HR portal with the intended last working day
respecting the notice period.

## Knowledge Transfer
The employee completes a handover document approved by the manager before exit. Access
revocation is initiated on the last working day.

## Exit Interview
An exit interview is conducted by HR for all voluntary separations. Feedback is
anonymised and aggregated.

## Asset Return
Laptop, ID card, tokens and other assets must be returned. Missing assets are recovered
at depreciated value from the final settlement.

Policy code: HR-EXIT-2026-01 | Owner: HR Operations team.
"""
},
{
 "bubble": "HR",
 "slug": "full_and_final_settlement",
 "title": "Full & Final Settlement",
 "body": """
## Components
F&F includes salary for days worked, leave encashment as per policy, variable pay where
eligible, gratuity where applicable and recovery of dues.

## Timeline
F&F is processed within 45 days of the last working day, subject to receipt of no-dues
certificate and asset return.

## Recoveries
Notice-period shortfall, outstanding advances, relocation recovery and excess leave are
recovered from the settlement.

## Form 16 & Documents
The relieving letter is issued with the settlement. Form 16 for the current year is
issued in June as per statute.

Policy code: HR-FNF-2026-01 | Owner: HR Operations team.
"""
},
{
 "bubble": "HR",
 "slug": "notice_period_policy",
 "title": "Notice Period Policy",
 "body": """
## Standard Notice
Notice period is 90 days for confirmed employees at M3 and above and 60 days for M1-M2.
Probationary employees serve 15 days.

## Buyout
The employee may buy out the notice period by paying basic salary for the unserved days.
Managers may waive part of the notice by mutual agreement.

## Garden Leave
In sensitive roles, the bank may place the employee on garden leave during notice, with
pay, while access is revoked.

## Exit Date Changes
The last working day can be preponed only by mutual written agreement.

Policy code: HR-NOTICE-2026-01 | Owner: HR Operations team.
"""
},
{
 "bubble": "HR",
 "slug": "retirement_and_superannuation",
 "title": "Retirement & Superannuation",
 "body": """
## Retirement Age
Superannuation is at 60 years. Extensions may be offered for identified specialists in
one-year increments up to age 62, approved by the CHRO.

## Pension and Provident Fund
Statutory provident fund and pension scheme benefits are settled as per EPFO rules on
superannuation.

## Gratuity
Gratuity is payable as per the Payment of Gratuity Act on superannuation without the
five-year minimum service condition.

## Transition Support
A pre-retirement counselling session and benefits orientation are offered in the final
year of service.

Policy code: HR-RET-2026-01 | Owner: Benefits team.
"""
},
{
 "bubble": "HR",
 "slug": "intern_and_trainee_policy",
 "title": "Intern & Trainee Policy",
 "body": """
## Engagement Types
Internships run 8 to 24 weeks. Management trainees join under structured one-year
programmes with defined rotations.

## Stipend
Interns receive a monthly stipend defined by the campus programme. Trainees receive a
fixed annual compensation with a defined confirmation path.

## Supervision
Every intern and trainee is assigned a mentor. Formal feedback is recorded at mid-point
and completion.

## Conversion
High-performing interns may be offered pre-placement offers subject to the
background-verification and joining processes.

Policy code: HR-INT-2026-01 | Owner: Talent Acquisition team.
"""
},
{
 "bubble": "HR",
 "slug": "employee_records_policy",
 "title": "Employee Records & Data Retention",
 "body": """
## Records Maintained
Personal file, compensation history, performance records, leave and attendance, benefits
elections and disciplinary records.

## Access Rights
Employees may request copies of their own records through the HR portal. Access to
others' records is restricted to authorised HR and audit roles.

## Retention
Employee records are retained as per statutory requirements. Payroll and tax records are
retained for the period prescribed by the Income-Tax Act.

## Disposal
Records beyond retention are destroyed through an approved destruction process with an
audit trail.

Policy code: HR-REC-2026-01 | Owner: HR Operations team.
"""
},
{
 "bubble": "HR",
 "slug": "dress_code_policy",
 "title": "Dress Code Policy",
 "body": """
## Business Attire
Corporate offices follow business formals from Monday to Thursday and business casuals on
Friday. Branch staff follow the prescribed uniform policy.

## Customer-Facing Roles
Customer-facing staff wear the bank-issued uniform or formal attire with the name badge
visible at all times.

## Special Days
Cultural and festival days allow traditional attire, subject to business norms and
local conventions.

## Hygiene and Presentation
Personal grooming and hygiene are expected to remain professional. Repeated violations
are addressed through the manager.

Policy code: HR-DRESS-2026-01 | Owner: Employee Relations team.
"""
},
{
 "bubble": "HR",
 "slug": "employee_transfers_policy",
 "title": "Employee Transfer Policy",
 "body": """
## Types of Transfer
- Business-driven: role or branch rebalancing.
- Rotation-based: planned movement for development or control requirements.
- Employee-requested: personal reasons, subject to vacancy.

## Notice
Business-driven transfers are communicated 30 days in advance. Emergency transfers may
be effective immediately with relocation support.

## Hardship Consideration
Employees with documented medical or caregiving constraints may request deferral through
the HRBP.

## Allowances
Transfers attract relocation support as per the relocation policy where applicable.

Policy code: HR-TRF-2026-01 | Owner: HR Operations team.
"""
},
]
