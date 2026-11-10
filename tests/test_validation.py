import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


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
            "RepaymentSchedule": 36936
        }

        for table, expected in expected_counts.items():
            actual = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            assert actual == expected

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


def test_all_five_anomalies_are_detectable():
    connection = get_connection()

    try:
        checks = [
            """
            SELECT COUNT(*)
            FROM LoanApplication a
            JOIN LoanProduct p ON a.product_id = p.product_id
            WHERE a.requested_term_months > p.max_term_months
               OR a.requested_term_months < p.min_term_months
            """,
            """
            SELECT COUNT(*)
            FROM RepaymentSchedule
            WHERE ABS(total_payment - principal_amount - interest_amount)
                  >= 0.01
            """,
            """
            SELECT COUNT(*)
            FROM Decision d
            JOIN AffordabilityCheck ac
                ON d.application_id = ac.application_id
            WHERE d.decided_at < ac.checked_at
            """,
            """
            SELECT COUNT(*)
            FROM (
                SELECT applicant_id
                FROM IncomeRecord
                GROUP BY applicant_id
                HAVING MAX(monthly_income) - MIN(monthly_income) > 0.01
            )
            """,
            """
            SELECT COUNT(*)
            FROM (
                SELECT application_id
                FROM DisbursementEvent
                WHERE disbursement_status = 'SUCCESS'
                GROUP BY application_id
                HAVING COUNT(*) > 1
            )
            """
        ]

        for query in checks:
            count = connection.execute(query).fetchone()[0]
            assert count >= 1

    finally:
        connection.close()