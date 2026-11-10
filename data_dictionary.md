
# Loan Management System – Data Dictionary

## 1. Applicant

| Field | Type | Required | Validation |
|---|---|---|---|
| applicant_id | TEXT | Yes | Unique primary key, APP-2026-XXXXXX |
| first_name | TEXT | Yes | Cannot be empty |
| last_name | TEXT | Yes | Cannot be empty |
| date_of_birth | DATE | Yes | Valid past date |
| email | TEXT | Yes | Valid email format |
| phone | TEXT | Yes | 10-digit phone number |
| city | TEXT | Yes | Cannot be empty |
| applicant_status | TEXT | Yes | ACTIVE, INACTIVE |
| created_at | DATETIME | Yes | Valid timestamp |

## 2. Employment

| Field | Type | Required | Validation |
|---|---|---|---|
| employment_id | TEXT | Yes | Primary key |
| applicant_id | TEXT | Yes | FK to Applicant |
| employer_name | TEXT | Yes | Cannot be empty |
| job_title | TEXT | Yes | Cannot be empty |
| employment_type | TEXT | Yes | PERMANENT, CONTRACT, SELF_EMPLOYED |
| start_date | DATE | Yes | Valid date |
| end_date | DATE | No | Must be after start_date |
| employment_status | TEXT | Yes | ACTIVE, ENDED |
| annual_salary | REAL | Yes | Greater than zero |

## 3. IncomeRecord

| Field | Type | Required | Validation |
|---|---|---|---|
| income_id | TEXT | Yes | Primary key |
| applicant_id | TEXT | Yes | FK to Applicant |
| employment_id | TEXT | No | FK to Employment |
| monthly_income | REAL | Yes | Greater than zero |
| income_source | TEXT | Yes | SALARY, BUSINESS, OTHER |
| proof_status | TEXT | Yes | VERIFIED, PENDING, MISSING, REJECTED |
| effective_from | DATE | Yes | Valid date |
| effective_to | DATE | No | Must be after effective_from |

## 4. CreditFacility

| Field | Type | Required | Validation |
|---|---|---|---|
| facility_id | TEXT | Yes | Primary key |
| applicant_id | TEXT | Yes | FK to Applicant |
| facility_type | TEXT | Yes | PERSONAL, HOME, AUTO, EDUCATION, CREDIT_CARD |
| outstanding_balance | REAL | Yes | Zero or greater |
| monthly_emi | REAL | Yes | Zero or greater |
| credit_score | INTEGER | Yes | 300–900 |
| facility_status | TEXT | Yes | ACTIVE, CLOSED |
| effective_date | DATE | Yes | Valid date |

## 5. LoanProduct

| Field | Type | Required | Validation |
|---|---|---|---|
| product_id | TEXT | Yes | Primary key |
| product_name | TEXT | Yes | Unique product name |
| min_amount | REAL | Yes | Greater than zero |
| max_amount | REAL | Yes | Greater than min_amount |
| annual_interest_rate | REAL | Yes | Greater than zero |
| min_term_months | INTEGER | Yes | Greater than zero |
| max_term_months | INTEGER | Yes | Greater than min_term_months |
| product_status | TEXT | Yes | ACTIVE, INACTIVE |

## 6. LoanApplication

| Field | Type | Required | Validation |
|---|---|---|---|
| application_id | TEXT | Yes | Primary key, LOAN-2026-XXXXXX |
| applicant_id | TEXT | Yes | FK to Applicant |
| product_id | TEXT | Yes | FK to LoanProduct |
| requested_amount | REAL | Yes | Greater than zero |
| requested_term_months | INTEGER | Yes | Greater than zero |
| application_date | DATE | Yes | Valid date |
| application_status | TEXT | Yes | SUBMITTED, CHECKED, APPROVED, REJECTED, MANUAL_REVIEW, DISBURSED |

## 7. Document

| Field | Type | Required | Validation |
|---|---|---|---|
| document_id | TEXT | Yes | Primary key, DOC-application-id-001 |
| application_id | TEXT | Yes | FK to LoanApplication |
| document_type | TEXT | Yes | ID_PROOF, INCOME_PROOF, ADDRESS_PROOF, BANK_STATEMENT |
| document_status | TEXT | Yes | SUBMITTED, VERIFIED, REJECTED, MISSING |
| submitted_at | DATETIME | No | Valid timestamp |
| verified_at | DATETIME | No | Must not precede submission |

## 8. AffordabilityCheck

| Field | Type | Required | Validation |
|---|---|---|---|
| check_id | TEXT | Yes | Primary key |
| application_id | TEXT | Yes | FK to LoanApplication |
| monthly_income | REAL | Yes | Greater than zero |
| existing_monthly_emi | REAL | Yes | Zero or greater |
| proposed_monthly_emi | REAL | Yes | Zero or greater |
| debt_to_income_ratio | REAL | Yes | Calculated percentage |
| disposable_income | REAL | Yes | Calculated amount |
| affordability_status | TEXT | Yes | PASS, FAIL, REVIEW |
| checked_at | DATETIME | Yes | Valid timestamp |

## 9. Decision

| Field | Type | Required | Validation |
|  ---  |---|---|---|
| decision_id | TEXT | Yes | Primary key, DEC-application-id-01 |
| application_id | TEXT | Yes | FK to LoanApplication |
| decision_status | TEXT | Yes | APPROVED, REJECTED, MANUAL_REVIEW |
| decision_reason | TEXT | Yes | Must explain decision |
| rule_inputs | TEXT | Yes | JSON containing rule inputs |
| decided_at | DATETIME | Yes | Must follow required checks |

## 10. RepaymentSchedule

| Field | Type | Required | Validation |
|---|---|---|---|
| schedule_id | TEXT | Yes | Primary key |
| application_id | TEXT | Yes | FK to LoanApplication |
| installment_number | INTEGER | Yes | Positive sequential number |
| due_date | DATE | Yes | Valid repayment date |
| principal_amount | REAL | Yes | Zero or greater |
| interest_amount | REAL | Yes | Zero or greater |
| total_payment | REAL | Yes | Principal + interest |
| outstanding_balance | REAL | Yes | Zero or greater |
| payment_status | TEXT | Yes | PENDING, PAID, OVERDUE |

---

## Relationships and Cardinality

1. Applicant → Employment: One-to-Many (1:N)
2. Applicant → IncomeRecord: One-to-Many (1:N)
3. Applicant → CreditFacility: One-to-Many (1:N)
4. Applicant → LoanApplication: One-to-Many (1:N)
5. LoanProduct → LoanApplication: One-to-Many (1:N)
6. LoanApplication → Document: One-to-Many (1:N)
7. LoanApplication → AffordabilityCheck: One-to-Many (1:N)
8. LoanApplication → Decision: One-to-Many (1:N)
9. LoanApplication → RepaymentSchedule: One-to-Many (1:N)

All primary keys must be unique and immutable.
All foreign keys must reference existing parent records.
Employment and income histories must preserve effective dates.
Decision and application state changes must retain their history.
