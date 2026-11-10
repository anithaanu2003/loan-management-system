import sqlite3
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def validate_database():
    connection = sqlite3.connect(DB_PATH)

    try:
        print("=" * 55)
        print("LOAN MANAGEMENT SYSTEM - VALIDATION REPORT")
        print("=" * 55)

        # 1. Record counts
        print("\n1. RECORD COUNTS")

        tables = [
            "Applicant",
            "Employment",
            "IncomeRecord",
            "CreditFacility",
            "LoanProduct",
            "LoanApplication",
            "Document",
            "AffordabilityCheck",
            "Decision",
            "RepaymentSchedule",
            "ApplicationEvent",
            "DisbursementEvent"
        ]

        for table in tables:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count}")

        # 2. Foreign key validation
        print("\n2. FOREIGN KEY VALIDATION")

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            print("FAILED:", foreign_key_errors)
        else:
            print("PASSED: No foreign key violations")

        # 3. Date consistency
        print("\n3. DATE VALIDATION")

        date_checks = {
            "Employment end date before start date": """
                SELECT COUNT(*) FROM Employment
                WHERE end_date IS NOT NULL
                AND end_date < start_date
            """,
            "Income end date before effective date": """
                SELECT COUNT(*) FROM IncomeRecord
                WHERE effective_to IS NOT NULL
                AND effective_to < effective_from
            """,
            "Document verified before submission": """
                SELECT COUNT(*) FROM Document
                WHERE verified_at IS NOT NULL
                AND submitted_at IS NOT NULL
                AND verified_at < submitted_at
            """
        }

        for description, query in date_checks.items():
            count = connection.execute(query).fetchone()[0]
            print(f"{description}: {count}")

        # 4. Business rule validation
        print("\n4. BUSINESS RULE VALIDATION")

        # Anomaly 1: Loan term outside product range
        term_errors = connection.execute("""
            SELECT a.application_id, a.requested_term_months,
                   p.min_term_months, p.max_term_months
            FROM LoanApplication a
            JOIN LoanProduct p ON a.product_id = p.product_id
            WHERE a.requested_term_months < p.min_term_months
               OR a.requested_term_months > p.max_term_months
        """).fetchall()

        print("\nANOM-001: Loan term outside product range")
        print("Detected records:", len(term_errors))
        for row in term_errors:
            print(row)

        # Anomaly 2: Repayment amount mismatch
        repayment_errors = connection.execute("""
            SELECT schedule_id, application_id,
                   principal_amount, interest_amount, total_payment
            FROM RepaymentSchedule
            WHERE ABS(
                total_payment - principal_amount - interest_amount
            ) >= 0.01
        """).fetchall()

        print("\nANOM-002: Repayment total mismatch")
        print("Detected records:", len(repayment_errors))
        for row in repayment_errors:
            print(row)

        # Anomaly 3: Decision before affordability check
        decision_errors = connection.execute("""
            SELECT d.decision_id, d.application_id,
                   d.decided_at, ac.checked_at
            FROM Decision d
            JOIN AffordabilityCheck ac
                ON d.application_id = ac.application_id
            WHERE d.decided_at < ac.checked_at
        """).fetchall()

        print("\nANOM-003: Decision before required check")
        print("Detected records:", len(decision_errors))
        for row in decision_errors:
            print(row)

        # Anomaly 4: Conflicting income records
        income_errors = connection.execute("""
            SELECT applicant_id,
                   MIN(monthly_income),
                   MAX(monthly_income),
                   COUNT(*)
            FROM IncomeRecord
            GROUP BY applicant_id
            HAVING MAX(monthly_income) - MIN(monthly_income) > 0.01
        """).fetchall()

        print("\nANOM-004: Conflicting income records")
        print("Detected applicants:", len(income_errors))
        for row in income_errors:
            print(row)

        # Anomaly 5: Duplicate successful disbursements
        disbursement_errors = connection.execute("""
            SELECT application_id, COUNT(*),
                   SUM(disbursed_amount)
            FROM DisbursementEvent
            WHERE disbursement_status = 'SUCCESS'
            GROUP BY application_id
            HAVING COUNT(*) > 1
        """).fetchall()

        print("\nANOM-005: Duplicate successful disbursements")
        print("Detected applications:", len(disbursement_errors))
        for row in disbursement_errors:
            print(row)
        # Anomaly 6: Duplicate loan applications
        duplicate_application_errors = connection.execute("""
            SELECT
                applicant_id,
                product_id,
                requested_amount,
                requested_term_months,
                application_date,
                COUNT(*) AS application_count,
                GROUP_CONCAT(application_id) AS application_ids
            FROM LoanApplication
            GROUP BY
                applicant_id,
                product_id,
                requested_amount,
                requested_term_months,
                application_date
            HAVING COUNT(*) > 1
        """).fetchall()

        print("\nANOM-006: Duplicate loan applications")
        print("Detected duplicate groups:", len(duplicate_application_errors))

        for row in duplicate_application_errors:
            print(row)

        print("\n" + "=" * 55)
        print("VALIDATION COMPLETED")
        print("=" * 55)

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate loan management database"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite database"
    )

    args = parser.parse_args()
    DB_PATH = Path(args.db).resolve()

    validate_database()