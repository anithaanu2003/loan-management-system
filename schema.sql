
-- =====================================================
-- LOAN MANAGEMENT SYSTEM
-- Database: SQLite
-- =====================================================

PRAGMA foreign_keys = ON;

-- 1. APPLICANT
CREATE TABLE IF NOT EXISTS Applicant (
    applicant_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    applicant_status TEXT NOT NULL
        CHECK (applicant_status IN ('ACTIVE', 'INACTIVE')),
    created_at TEXT NOT NULL
);

-- 2. EMPLOYMENT
CREATE TABLE IF NOT EXISTS Employment (
    employment_id TEXT PRIMARY KEY,
    applicant_id TEXT NOT NULL,
    employer_name TEXT NOT NULL,
    job_title TEXT NOT NULL,
    employment_type TEXT NOT NULL
        CHECK (employment_type IN (
            'PERMANENT', 'CONTRACT', 'SELF_EMPLOYED'
        )),
    start_date TEXT NOT NULL,
    end_date TEXT,
    employment_status TEXT NOT NULL
        CHECK (employment_status IN ('ACTIVE', 'ENDED')),
    annual_salary REAL NOT NULL CHECK (annual_salary > 0),

    FOREIGN KEY (applicant_id)
        REFERENCES Applicant(applicant_id),

    CHECK (end_date IS NULL OR end_date >= start_date)
);

-- 3. INCOME RECORD
CREATE TABLE IF NOT EXISTS IncomeRecord (
    income_id TEXT PRIMARY KEY,
    applicant_id TEXT NOT NULL,
    employment_id TEXT,
    monthly_income REAL NOT NULL CHECK (monthly_income > 0),
    income_source TEXT NOT NULL
        CHECK (income_source IN ('SALARY', 'BUSINESS', 'OTHER')),
    proof_status TEXT NOT NULL
        CHECK (proof_status IN (
            'VERIFIED', 'PENDING', 'MISSING', 'REJECTED'
        )),
    effective_from TEXT NOT NULL,
    effective_to TEXT,

    FOREIGN KEY (applicant_id)
        REFERENCES Applicant(applicant_id),

    FOREIGN KEY (employment_id)
        REFERENCES Employment(employment_id),

    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- 4. CREDIT FACILITY
CREATE TABLE IF NOT EXISTS CreditFacility (
    facility_id TEXT PRIMARY KEY,
    applicant_id TEXT NOT NULL,
    facility_type TEXT NOT NULL
        CHECK (facility_type IN (
            'PERSONAL', 'HOME', 'AUTO',
            'EDUCATION', 'CREDIT_CARD'
        )),
    outstanding_balance REAL NOT NULL
        CHECK (outstanding_balance >= 0),
    monthly_emi REAL NOT NULL CHECK (monthly_emi >= 0),
    credit_score INTEGER NOT NULL
        CHECK (credit_score BETWEEN 300 AND 900),
    facility_status TEXT NOT NULL
        CHECK (facility_status IN ('ACTIVE', 'CLOSED')),
    effective_date TEXT NOT NULL,

    FOREIGN KEY (applicant_id)
        REFERENCES Applicant(applicant_id)
);

-- 5. LOAN PRODUCT
CREATE TABLE IF NOT EXISTS LoanProduct (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL UNIQUE,
    min_amount REAL NOT NULL CHECK (min_amount > 0),
    max_amount REAL NOT NULL,
    annual_interest_rate REAL NOT NULL
        CHECK (annual_interest_rate > 0),
    min_term_months INTEGER NOT NULL
        CHECK (min_term_months > 0),
    max_term_months INTEGER NOT NULL,
    product_status TEXT NOT NULL
        CHECK (product_status IN ('ACTIVE', 'INACTIVE')),

    CHECK (max_amount > min_amount),
    CHECK (max_term_months >= min_term_months)
);

-- 6. LOAN APPLICATION
CREATE TABLE IF NOT EXISTS LoanApplication (
    application_id TEXT PRIMARY KEY,
    applicant_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    requested_amount REAL NOT NULL
        CHECK (requested_amount > 0),
    requested_term_months INTEGER NOT NULL
        CHECK (requested_term_months > 0),
    application_date TEXT NOT NULL,
    application_status TEXT NOT NULL
        CHECK (application_status IN (
            'SUBMITTED', 'CHECKED', 'APPROVED',
            'REJECTED', 'MANUAL_REVIEW', 'DISBURSED'
        )),

    FOREIGN KEY (applicant_id)
        REFERENCES Applicant(applicant_id),

    FOREIGN KEY (product_id)
        REFERENCES LoanProduct(product_id)
);

-- 7. DOCUMENT
CREATE TABLE IF NOT EXISTS Document (
    document_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    document_type TEXT NOT NULL
        CHECK (document_type IN (
            'ID_PROOF', 'INCOME_PROOF',
            'ADDRESS_PROOF', 'BANK_STATEMENT'
        )),
    document_status TEXT NOT NULL
        CHECK (document_status IN (
            'SUBMITTED', 'VERIFIED', 'REJECTED', 'MISSING'
        )),
    submitted_at TEXT,
    verified_at TEXT,

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id),

    CHECK (
        verified_at IS NULL OR submitted_at IS NULL
        OR verified_at >= submitted_at
    )
);

-- 8. AFFORDABILITY CHECK
CREATE TABLE IF NOT EXISTS AffordabilityCheck (
    check_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    monthly_income REAL NOT NULL CHECK (monthly_income > 0),
    existing_monthly_emi REAL NOT NULL
        CHECK (existing_monthly_emi >= 0),
    proposed_monthly_emi REAL NOT NULL
        CHECK (proposed_monthly_emi >= 0),
    debt_to_income_ratio REAL NOT NULL
        CHECK (debt_to_income_ratio >= 0),
    disposable_income REAL NOT NULL,
    affordability_status TEXT NOT NULL
        CHECK (affordability_status IN ('PASS', 'FAIL', 'REVIEW')),
    checked_at TEXT NOT NULL,

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id)
);

-- 9. DECISION
CREATE TABLE IF NOT EXISTS Decision (
    decision_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    decision_status TEXT NOT NULL
        CHECK (decision_status IN (
            'APPROVED', 'REJECTED', 'MANUAL_REVIEW'
        )),
    decision_reason TEXT NOT NULL,
    rule_inputs TEXT NOT NULL,
    decided_at TEXT NOT NULL,

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id)
);

-- 10. REPAYMENT SCHEDULE
CREATE TABLE IF NOT EXISTS RepaymentSchedule (
    schedule_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    installment_number INTEGER NOT NULL
        CHECK (installment_number > 0),
    due_date TEXT NOT NULL,
    principal_amount REAL NOT NULL
        CHECK (principal_amount >= 0),
    interest_amount REAL NOT NULL
        CHECK (interest_amount >= 0),
    total_payment REAL NOT NULL
        CHECK (total_payment >= 0),
    outstanding_balance REAL NOT NULL
        CHECK (outstanding_balance >= 0),
    payment_status TEXT NOT NULL
        CHECK (payment_status IN (
            'PENDING', 'PAID', 'OVERDUE'
        )),

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id),

    UNIQUE (application_id, installment_number)
);


-- =====================================================
-- SUPPORTING EVENT HISTORY TABLES
-- =====================================================

-- Application status changes: preserve every transition.
CREATE TABLE IF NOT EXISTS ApplicationEvent (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    event_timestamp TEXT NOT NULL,
    event_reason TEXT,

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id)
);

-- Disbursement history: supports duplicate detection.
CREATE TABLE IF NOT EXISTS DisbursementEvent (
    disbursement_id TEXT PRIMARY KEY,
    application_id TEXT NOT NULL,
    disbursed_amount REAL NOT NULL
        CHECK (disbursed_amount > 0),
    disbursement_status TEXT NOT NULL
        CHECK (disbursement_status IN (
            'SUCCESS', 'FAILED', 'REVERSED'
        )),
    disbursed_at TEXT NOT NULL,
    transaction_reference TEXT NOT NULL,

    FOREIGN KEY (application_id)
        REFERENCES LoanApplication(application_id)
);

-- =====================================================
-- INDEXES FOR FASTER QUERIES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_employment_applicant
ON Employment(applicant_id);

CREATE INDEX IF NOT EXISTS idx_income_applicant
ON IncomeRecord(applicant_id);

CREATE INDEX IF NOT EXISTS idx_credit_applicant
ON CreditFacility(applicant_id);

CREATE INDEX IF NOT EXISTS idx_application_applicant
ON LoanApplication(applicant_id);

CREATE INDEX IF NOT EXISTS idx_application_product
ON LoanApplication(product_id);

CREATE INDEX IF NOT EXISTS idx_document_application
ON Document(application_id);

CREATE INDEX IF NOT EXISTS idx_affordability_application
ON AffordabilityCheck(application_id);

CREATE INDEX IF NOT EXISTS idx_decision_application
ON Decision(application_id);

CREATE INDEX IF NOT EXISTS idx_schedule_application
ON RepaymentSchedule(application_id);

CREATE INDEX IF NOT EXISTS idx_application_events
ON ApplicationEvent(application_id);

CREATE INDEX IF NOT EXISTS idx_disbursement_application
ON DisbursementEvent(application_id);