# Loan Application Management and Risk Assessment System

## Project Overview

A Python and SQLite-based loan application management and risk assessment system. It generates synthetic banking data, evaluates loan affordability, produces rule-based loan decisions, creates repayment schedules, detects data anomalies, and exports datasets for analysis.

## Technology Stack

- Python 3.13
- SQLite
- SQL
- CSV and JSON
- Pytest

## Project Structure

```text
loan-management-system/
├── data/
│   └── exports/
|           |
|           |--Applicant.csv
|           |--Applicant.json
|           |--LoanApplication.csv
|           |--LoanApplication.json
|           |--seed_data.sql
|           |--source_manifest.json
|           |-- validation_summary.json
├── ground_truth/
│   ├── ground_truth.csv
│   └── ground_truth.json
├── src/
│   ├── data_generator.py
│   ├── database.py
│   ├── affordability.py
│   ├── decision_engine.py
│   ├── repayment.py
│   ├── anomaly_detection.py
│   ├── validation.py
│   └── export_data.py
├── tests/
│   └── test_validation.py
├── schema.sql
├── data_dictionary.md
├── requirements.txt
└── README.md
```

## Dataset

- 10,000 synthetic applicants
- 10,000 employment records
- 10,001 income records
- 12,063 credit facilities
- 4 loan products
- 6,000 loan applications
- 24,000 documents
- 6,000 affordability checks
- 6,000 decisions
- 36,936 repayment schedule records

Random seed: `20261022`

## Loan Decision Outcomes

| Decision | Applications |
|---|---:|
| Approved | 408 |
| Manual Review | 1,717 |
| Rejected | 3,875 |
| Total | 6,000 |

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the database:

```bash
python src/database.py
```

## Execution

Run the scripts in this order:

```bash
python src/data_generator.py
python src/affordability.py
python src/decision_engine.py
python src/repayment.py
python src/anomaly_detection.py
python src/validation.py
python src/export_data.py
```

**Important:** Run `anomaly_detection.py` only once after generating the baseline data. It deliberately introduces five labelled anomalies.

## Anomaly Scenarios

1. Loan term outside the product's permitted range.
2. Repayment schedule total does not reconcile with principal and interest.
3. Decision timestamp precedes the required affordability check.
4. Conflicting income records for the same applicant.
5. Duplicate successful disbursements for one application.

Anomaly labels are maintained separately in the `ground_truth` directory and are not used as decision-engine features.

## Validation

The validation script checks:

- Foreign-key integrity
- Date consistency
- Loan product term limits
- Repayment arithmetic
- Decision chronology
- Conflicting income records
- Duplicate successful disbursements

## Data Provenance

All generated records are synthetic and created using a fixed random seed. No real customer records or protected personal attributes are used for loan eligibility decisions.

## Exports

CSV, JSON, and SQL seed data are available in:

```text
data/exports/
```

## Limitations

This is a synthetic-data engineering and rule-based assessment project. Its decisions are illustrative and are not intended for real-world lending or credit approval. 