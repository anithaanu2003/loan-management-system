# Loan Application Management System

A Python and SQLite-based loan application management system that generates synthetic loan data, evaluates affordability, makes rule-based loan decisions, creates repayment schedules, manages disbursement eligibility, detects data anomalies, and exports validated datasets.

## Project Overview

This project simulates an end-to-end loan application processing workflow, from applicant and financial data management to affordability assessment, decision generation, repayment scheduling, and disbursement eligibility.

It demonstrates relational database design, synthetic data generation, financial calculations, rule-based decision-making, data validation, anomaly detection, event tracking, and data export.

**Dataset scale:**

- 10,000 synthetic applicants
- 6,000 loan applications
- 4 loan products
- 12 relational database tables
- 6 anomaly categories

All data is synthetic and created for demonstration and testing purposes. No real customer or financial information is used.

## Key Features

### 1. Relational Database Management

- Designed a relational database using SQLite.
- Implemented primary keys, foreign keys, constraints, and relationships.
- Maintained application lifecycle and disbursement event records.
- Structured data across 12 tables.

### 2. Synthetic Data Generation

- Generated 10,000 applicants and 6,000 loan applications.
- Created employment, income, credit facility, loan product, and document records.
- Used a fixed random seed (`20261022`) for reproducibility.
- Supported configurable applicant and application counts.
- Included missing documents, duplicate applications, and different financial risk scenarios.

### 3. Affordability Assessment

- Calculated proposed monthly loan EMIs.
- Evaluated existing and proposed EMI obligations.
- Calculated debt-to-income ratios and disposable income.
- Classified affordability results as `PASS`, `REVIEW`, or `FAIL`.

### 4. Rule-Based Loan Decision Engine

Generated one decision for each loan application using affordability results, credit score, income proof, employment status, and document verification.

Possible outcomes:

- `APPROVED`
- `REJECTED`
- `MANUAL_REVIEW`

The decision engine also records decision reasons and application status changes.

### 5. Repayment Schedule Generation

- Generated repayment schedules for approved applications.
- Calculated monthly EMI, interest, principal, and outstanding balance.
- Generated monthly repayment due dates.

### 6. Disbursement Management

- Checked disbursement eligibility using application status and decision results.
- Verified affordability status and all four required documents.
- Checked repayment schedule completeness.
- Recorded successful disbursement events with transaction references.
- Prevented repeated successful disbursements.
- Updated application status to `DISBURSED`.
- Maintained application event history for traceability.

### 7. Anomaly Injection and Detection

Implemented six anomaly categories:

| Anomaly ID | Description |
|---|---|
| ANOM-001 | Loan term outside the product's permitted range |
| ANOM-002 | Repayment schedule total does not reconcile |
| ANOM-003 | Decision recorded before the required affordability check |
| ANOM-004 | Conflicting income records for an applicant |
| ANOM-005 | Duplicate successful disbursement events |
| ANOM-006 | Duplicate loan applications |

Known anomalies and expected anomaly details are stored separately in ground-truth CSV and JSON files. Ground-truth information is not used as a decision-engine feature.

### 8. Data Validation

The validation script checks:

- Database table record counts.
- Foreign-key integrity.
- Employment, income, and document date consistency.
- Loan term violations.
- Repayment amount mismatches.
- Decision timing violations.
- Conflicting income records.
- Duplicate successful disbursements.
- Duplicate loan application groups.

### 9. Data Export

Exports all 12 database tables into:

- CSV files
- JSON files
- SQL seed data

Additional metadata files:

- `source_manifest.json`
- `validation_summary.json`

The SQL seed export can be used to recreate the exported database.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.13 | Application logic and data processing |
| SQLite | Relational database |
| SQL | Database queries and data management |
| CSV | Structured data export |
| JSON | Structured data and metadata export |
| pytest | Automated testing |
| Git and GitHub | Version control and project hosting |

## Database Tables

The database contains 12 tables:

| Table | Description |
|---|---|
| Applicant | Applicant information |
| Employment | Employment details |
| IncomeRecord | Income information and verification |
| CreditFacility | Existing credit facilities |
| LoanProduct | Available loan products |
| LoanApplication | Loan application details |
| Document | Applicant document records |
| AffordabilityCheck | Affordability assessment results |
| Decision | Loan decision records |
| RepaymentSchedule | Repayment details |
| ApplicationEvent | Application lifecycle events |
| DisbursementEvent | Disbursement event records |

## Project Structure

```text
loan-management-system/
│
├── data/
│   └── exports/
│       ├── full_test/
│       │   ├── CSV exports
│       │   ├── JSON exports
│       │   ├── seed_data.sql
│       │   ├── source_manifest.json
│       │   └── validation_summary.json
│       │
│       └── Original exports
│
├── ground_truth/
│   ├── ground_truth.csv
│   ├── ground_truth.json
│   └── full_test/
│       ├── ground_truth.csv
│       └── ground_truth.json
│
├── src/
│   ├── database.py
│   ├── data_generator.py
│   ├── affordability.py
│   ├── decision_engine.py
│   ├── repayment.py
│   ├── disbursement.py
│   ├── anomaly_detection.py
│   ├── validation.py
│   └── export_data.py
│
├── tests/
│   └── test_validation.py
│
├── schema.sql
├── data_dictionary.md
├── requirements.txt
├── README.md
└── .gitignore
```

The SQLite database files are generated locally and excluded from Git using `.gitignore`.

## Installation and Setup

### Prerequisites

- Python 3.13 or compatible Python version
- Git
- Visual Studio Code or another Python editor

### 1. Clone the repository

```bash
git clone https://github.com/anithaanu2003/loan-management-system.git
```

```bash
cd loan-management-system
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the database

```bash
python -c "import sqlite3; c=sqlite3.connect('data/loan_management.db'); c.executescript(open('schema.sql', encoding='utf-8').read()); c.close(); print('Database initialized successfully')"
```

## Running the Project

Run the scripts in the following order.

### 1. Generate synthetic data

```bash
python src/data_generator.py --applicants 10000 --applications 6000
```

### 2. Generate affordability checks

```bash
python src/affordability.py
```

### 3. Generate loan decisions

```bash
python src/decision_engine.py
```

### 4. Generate repayment schedules

```bash
python src/repayment.py
```

### 5. Check disbursement eligibility

Check whether an approved application is eligible for disbursement:

```bash
python src/disbursement.py --application-id LOAN-2026-XXXXXX --action check
```

Replace the example application ID with an actual application ID from the generated database.

The eligibility check verifies:

- Application approval status.
- Approved decision record.
- Passed affordability assessment.
- Verification of all four required documents.
- Completeness of the repayment schedule.
- Absence of an existing successful disbursement.

### 6. Record a disbursement

For an eligible application, record the successful disbursement:

```bash
python src/disbursement.py --application-id LOAN-2026-XXXXXX --action disburse --transaction-reference TXN-2026-000001
```

The system records the disbursement, updates the application status to `DISBURSED`, and creates an application lifecycle event.

A second successful disbursement for the same application is prevented.

### 7. Inject known anomalies and generate ground truth

```bash
python src/anomaly_detection.py
```

**Important:** Run anomaly injection only once on a clean generated database. It modifies database records to introduce known anomalies, including duplicate successful disbursement events.

### 8. Validate the database

```bash
python src/validation.py
```

### 9. Export the data

```bash
python src/export_data.py
```

The default database is `data/loan_management.db`, and the default export directory is `data/exports`.

## Running with a Separate Database

The data-generation and processing scripts support a `--db` argument. For example:

```bash
python src/data_generator.py --applicants 10000 --applications 6000 --db data/full_test.db
```

Use the same database path for the subsequent processing scripts.

To generate affordability checks, decisions, and repayment schedules:

```bash
python src/affordability.py --db data/full_test.db
```

```bash
python src/decision_engine.py --db data/full_test.db
```

```bash
python src/repayment.py --db data/full_test.db
```

To check disbursement eligibility:

```bash
python src/disbursement.py --db data/full_test.db --application-id LOAN-2026-XXXXXX --action check
```

To export that database separately:

```bash
python src/export_data.py --db data/full_test.db --export-dir data/exports/full_test
```

For anomaly injection into a separate test database:

```bash
python src/anomaly_detection.py --db data/full_test.db --ground-truth-dir ground_truth/full_test
```

## Full-Scale Dataset Results

The completed full-scale pipeline produced the following results:

| Dataset | Records |
|---|---:|
| Applicant | 10,000 |
| Employment | 10,000 |
| IncomeRecord | 10,001 |
| CreditFacility | 12,063 |
| LoanProduct | 4 |
| LoanApplication | 6,000 |
| Document | 24,000 |
| AffordabilityCheck | 6,000 |
| Decision | 6,000 |
| RepaymentSchedule | 32,863 |
| ApplicationEvent | 6,000 |
| DisbursementEvent | 2 |

**Note:** These figures represent the previously completed full-scale pipeline before the new normal disbursement workflow was tested against the full-scale database.

### Loan Decision Distribution

| Decision | Applications |
|---|---:|
| APPROVED | 379 |
| MANUAL_REVIEW | 1,778 |
| REJECTED | 3,843 |
| **Total** | **6,000** |

### Anomaly Detection Results

| Anomaly | Detected |
|---|---:|
| ANOM-001 | 1 |
| ANOM-002 | 1 |
| ANOM-003 | 1 |
| ANOM-004 | 1 |
| ANOM-005 | 1 |
| ANOM-006 | 60 duplicate groups |
| **Total ground-truth records** | **65** |

All 65 known anomaly records were detected in the full-scale validation run.

## Disbursement Workflow Testing

The normal disbursement workflow was tested using an isolated test database.

Verified test cases:

1. Eligible approved application successfully disbursed.
2. Repeated disbursement attempt blocked.
3. Rejected application disbursement prevented.
4. Application status updated to `DISBURSED`.
5. Application event history recorded as `APPROVED` to `DISBURSED`.
6. Command-line eligibility check correctly identified an existing successful disbursement.

These tests demonstrate the normal disbursement workflow. Full-scale disbursement testing remains separate.

## Automated Testing

The project uses pytest for automated testing.

Run:

```bash
python -m pytest -v
```

Previously recorded test results:

```text
4 passed in 0.43s
```

Tests cover:

1. Database existence.
2. Expected record counts.
3. Foreign-key integrity.
4. Detection of all five individually injected anomaly types.

The recorded test results should be refreshed after any code or test changes.

## Data Provenance and Reproducibility

- All generated records are synthetic.
- The random seed is `20261022`.
- The generator supports configurable dataset sizes.
- Ground-truth anomaly records are maintained separately from decision inputs.
- The source manifest records data provenance, seed, exported tables, and record counts.
- SQL seed data is included in the full-scale export folder.

## Limitations

- Loan decisions use demonstration rule-based logic, not a production credit-risk model.
- No real credit bureau or external financial institution is connected.
- The disbursement workflow simulates successful disbursement recording; it does not connect to real banking or payment systems.
- The system uses synthetic data and is not intended for actual lending decisions.
- The validation summary export is a recorded summary of the completed validation results.

## Future Improvements

- Add more comprehensive lifecycle and business-rule validation.
- Automate generation of validation summary reports.
- Add more test cases for boundary conditions and invalid data.
- Extend anomaly detection and reporting.
- Integrate with external payment systems in a simulated environment.

## Author

**Anitha Anumolu**

GitHub: [anithaanu2003](https://github.com/anithaanu2003)

Repository: [Loan Application Management System](https://github.com/anithaanu2003/loan-management-system)

---

*This project was developed as a synthetic-data engineering and loan decision workflow demonstration.*