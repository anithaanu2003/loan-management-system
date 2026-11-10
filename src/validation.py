
import sqlite3
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def validate_database():

    connection = sqlite3.connect(DB_PATH)

    try:
        print("=" * 60)
        print("LOAN MANAGEMENT SYSTEM - VALIDATION REPORT")
        print("=" * 60)

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

        print("Foreign key violations:", len(foreign_key_errors))

        for error in foreign_key_errors:
            print(error)

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

        # 4. Application lifecycle validation
        print("\n4. APPLICATION LIFECYCLE VALIDATION")

        lifecycle_errors = connection.execute("""
            SELECT
                a.application_id,
                a.application_status,
                e.new_status AS latest_event_status
            FROM LoanApplication a
            LEFT JOIN ApplicationEvent e
                ON e.application_id = a.application_id
                AND e.event_timestamp = (
                    SELECT MAX(e2.event_timestamp)
                    FROM ApplicationEvent e2
                    WHERE e2.application_id = a.application_id
                )
            WHERE e.new_status IS NULL
               OR a.application_status != e.new_status
        """).fetchall()

        print("Lifecycle inconsistencies:", len(lifecycle_errors))

        for row in lifecycle_errors:
            print(row)

        # 5. Disbursement workflow validation
        print("\n5. DISBURSEMENT WORKFLOW VALIDATION")

        disbursement_errors = connection.execute("""
            SELECT
                d.disbursement_id,
                d.application_id,
                a.application_status,
                d.disbursement_status
            FROM DisbursementEvent d
            JOIN LoanApplication a
                ON d.application_id = a.application_id
            WHERE d.disbursement_status = 'SUCCESS'
              AND a.application_status != 'DISBURSED'
              AND NOT EXISTS (
                  SELECT 1
                  FROM DisbursementEvent duplicate
                  WHERE duplicate.application_id = d.application_id
                    AND duplicate.disbursement_status = 'SUCCESS'
                  GROUP BY duplicate.application_id
                  HAVING COUNT(*) > 1
              )
        """).fetchall()

        print(
            "Unexpected successful disbursements with incorrect application status:",
            len(disbursement_errors)
        )

        for row in disbursement_errors:
            print(row)

        # Check whether DISBURSED applications have a successful event.
        missing_disbursement_events = connection.execute("""
            SELECT a.application_id
            FROM LoanApplication a
            WHERE a.application_status = 'DISBURSED'
              AND NOT EXISTS (
                  SELECT 1
                  FROM DisbursementEvent d
                  WHERE d.application_id = a.application_id
                    AND d.disbursement_status = 'SUCCESS'
              )
        """).fetchall()

        print(
            "DISBURSED applications without successful events:",
            len(missing_disbursement_events)
        )

        for row in missing_disbursement_events:
            print(row)

        # 6. Business rule and anomaly validation
        print("\n6. BUSINESS RULE AND ANOMALY VALIDATION")

        # ANOM-001: Loan term outside product range
        term_errors = connection.execute("""
            SELECT
                a.application_id,
                a.requested_term_months,
                p.min_term_months,
                p.max_term_months
            FROM LoanApplication a
            JOIN LoanProduct p
                ON a.product_id = p.product_id
            WHERE a.requested_term_months < p.min_term_months
               OR a.requested_term_months > p.max_term_months
        """).fetchall()

        print("\nANOM-001: Loan term outside product range")
        print("Detected records:", len(term_errors))

        for row in term_errors:
            print(row)

        # ANOM-002: Repayment amount mismatch
        repayment_errors = connection.execute("""
            SELECT
                schedule_id,
                application_id,
                principal_amount,
                interest_amount,
                total_payment
            FROM RepaymentSchedule
            WHERE ABS(
                total_payment - principal_amount - interest_amount
            ) >= 0.01
        """).fetchall()

        print("\nANOM-002: Repayment total mismatch")
        print("Detected records:", len(repayment_errors))

        for row in repayment_errors:
            print(row)

        # ANOM-003: Decision before affordability check
        decision_errors = connection.execute("""
            SELECT
                d.decision_id,
                d.application_id,
                d.decided_at,
                ac.checked_at
            FROM Decision d
            JOIN AffordabilityCheck ac
                ON d.application_id = ac.application_id
            WHERE d.decided_at < ac.checked_at
        """).fetchall()

        print("\nANOM-003: Decision before required check")
        print("Detected records:", len(decision_errors))

        for row in decision_errors:
            print(row)

        # ANOM-004: Conflicting income records
        income_errors = connection.execute("""
            SELECT
                applicant_id,
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

        # ANOM-005: Duplicate successful disbursements
        duplicate_disbursements = connection.execute("""
            SELECT
                application_id,
                COUNT(*),
                SUM(disbursed_amount)
            FROM DisbursementEvent
            WHERE disbursement_status = 'SUCCESS'
            GROUP BY application_id
            HAVING COUNT(*) > 1
        """).fetchall()

        print("\nANOM-005: Duplicate successful disbursements")
        print("Detected applications:", len(duplicate_disbursements))

        for row in duplicate_disbursements:
            print(row)

        # ANOM-006: Duplicate loan applications
        duplicate_applications = connection.execute("""
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
        print("Detected duplicate groups:", len(duplicate_applications))

        for row in duplicate_applications:
            print(row)

        # 7. Final report
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        print("Foreign key violations:", len(foreign_key_errors))
        print("Lifecycle inconsistencies:", len(lifecycle_errors))
        print("Disbursement status inconsistencies:", len(disbursement_errors))
        print(
            "Missing successful disbursement events:",
            len(missing_disbursement_events)
        )

        print("\nKnown anomaly detection results:")
        print("ANOM-001:", len(term_errors))
        print("ANOM-002:", len(repayment_errors))
        print("ANOM-003:", len(decision_errors))
        print("ANOM-004:", len(income_errors))
        print("ANOM-005:", len(duplicate_disbursements))
        print("ANOM-006:", len(duplicate_applications))

        print("\nVALIDATION COMPLETED")
        print("=" * 60)

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
