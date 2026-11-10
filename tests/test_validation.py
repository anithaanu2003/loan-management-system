import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "full_test.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def test_database_exists():
    assert DB_PATH.exists()


def test_expected_record_counts():
    connection = get_connection()

    try:
        expected_counts = {
            "Applicant": 10000,
            "LoanApplication": 6000,
            "LoanProduct": 4,
            "AffordabilityCheck": 6000,
            "Decision": 6000,
            "RepaymentSchedule": 32863
        }

        for table, expected in expected_counts.items():
            actual = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert actual == expected, (
                f"{table}: expected {expected}, found {actual}"
            )

    finally:
        connection.close()


def test_foreign_key_integrity():
    connection = get_connection()

    try:
        errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        assert errors == []

    finally:
        connection.close()


def test_all_six_anomalies_are_detectable():
    connection = get_connection()

    try:
        checks = {
            "ANOM-001: Invalid loan term": """
                SELECT COUNT(*)
                FROM LoanApplication a
                JOIN LoanProduct p ON a.product_id = p.product_id
                WHERE a.requested_term_months > p.max_term_months
                   OR a.requested_term_months < p.min_term_months
            """,

            "ANOM-002: Repayment mismatch": """
                SELECT COUNT(*)
                FROM RepaymentSchedule
                WHERE ABS(
                    total_payment - principal_amount - interest_amount
                ) >= 0.01
            """,

            "ANOM-003: Decision before affordability check": """
                SELECT COUNT(*)
                FROM Decision d
                JOIN AffordabilityCheck ac
                    ON d.application_id = ac.application_id
                WHERE d.decided_at < ac.checked_at
            """,

            "ANOM-004: Conflicting income records": """
                SELECT COUNT(*)
                FROM (
                    SELECT applicant_id
                    FROM IncomeRecord
                    GROUP BY applicant_id
                    HAVING MAX(monthly_income) - MIN(monthly_income) > 0.01
                )
            """,

            "ANOM-005: Duplicate successful disbursement": """
                SELECT COUNT(*)
                FROM (
                    SELECT application_id
                    FROM DisbursementEvent
                    WHERE disbursement_status = 'SUCCESS'
                    GROUP BY application_id
                    HAVING COUNT(*) > 1
                )
            """,

            "ANOM-006: Duplicate loan applications": """
                SELECT COUNT(*)
                FROM (
                    SELECT applicant_id, product_id, requested_amount,
                           requested_term_months, application_date
                    FROM LoanApplication
                    GROUP BY applicant_id, product_id, requested_amount,
                             requested_term_months, application_date
                    HAVING COUNT(*) > 1
                )
            """
        }

        for anomaly, query in checks.items():
            count = connection.execute(query).fetchone()[0]

            assert count >= 1, (
                f"{anomaly} was not detected"
            )

            print(f"{anomaly}: {count} detected")

    finally:
        connection.close()