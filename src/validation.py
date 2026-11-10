
import sqlite3
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"

TABLES = [
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


def validate_database(db_path=None):

    target_db = Path(db_path).resolve() if db_path else DB_PATH
    connection = sqlite3.connect(target_db)

    try:
        report = {
            "database": str(target_db),
            "record_counts": {},
            "foreign_key_violations": 0,
            "date_validation": {},
            "lifecycle_inconsistencies": 0,
            "disbursement_status_inconsistencies": 0,
            "missing_successful_disbursement_events": 0,
            "detected_anomalies": {}
        }

        print("=" * 60)
        print("LOAN MANAGEMENT SYSTEM - VALIDATION REPORT")
        print("=" * 60)

        # 1. Record counts
        print("\n1. RECORD COUNTS")

        for table in TABLES:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

            report["record_counts"][table] = count
            print(f"{table}: {count}")

        # 2. Foreign key validation
        print("\n2. FOREIGN KEY VALIDATION")

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        report["foreign_key_violations"] = len(foreign_key_errors)

        print("Foreign key violations:", len(foreign_key_errors))

        for error in foreign_key_errors:
            print(error)

        # 3. Date consistency
        print("\n3. DATE VALIDATION")

        date_checks = {
            "invalid_employment_dates": """
                SELECT COUNT(*) FROM Employment
                WHERE end_date IS NOT NULL
                AND end_date < start_date
            """,

            "invalid_income_dates": """
                SELECT COUNT(*) FROM IncomeRecord
                WHERE effective_to IS NOT NULL
                AND effective_to < effective_from
            """,

            "invalid_document_dates": """
                SELECT COUNT(*) FROM Document
                WHERE verified_at IS NOT NULL
                AND submitted_at IS NOT NULL
                AND verified_at < submitted_at
            """
        }

        for name, query in date_checks.items():
            count = connection.execute(query).fetchone()[0]
            report["date_validation"][name] = count
            print(f"{name}: {count}")

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

        report["lifecycle_inconsistencies"] = len(lifecycle_errors)

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

        report["disbursement_status_inconsistencies"] = len(
            disbursement_errors
        )

        print(
            "Unexpected successful disbursements with incorrect application status:",
            len(disbursement_errors)
        )

        for row in disbursement_errors:
            print(row)

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

        report["missing_successful_disbursement_events"] = len(
            missing_disbursement_events
        )

        print(
            "DISBURSED applications without successful events:",
            len(missing_disbursement_events)
        )

        for row in missing_disbursement_events:
            print(row)

        # 6. Business rule and anomaly validation
        print("\n6. BUSINESS RULE AND ANOMALY VALIDATION")

        # ANOM-001
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

        # ANOM-002
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

        # ANOM-003
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

        # ANOM-004
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

        # ANOM-005
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

        # ANOM-006
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

        # Store anomaly counts in the report
        report["detected_anomalies"] = {
            "term_outside_product_range": len(term_errors),
            "repayment_total_mismatch": len(repayment_errors),
            "decision_before_required_check": len(decision_errors),
            "conflicting_income_records": len(income_errors),
            "duplicate_successful_disbursement": len(duplicate_disbursements),
            "duplicate_loan_application_groups": len(duplicate_applications)
        }

        # 7. Final report
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        print("Foreign key violations:", report["foreign_key_violations"])
        print("Lifecycle inconsistencies:", report["lifecycle_inconsistencies"])
        print(
            "Disbursement status inconsistencies:",
            report["disbursement_status_inconsistencies"]
        )
        print(
            "Missing successful disbursement events:",
            report["missing_successful_disbursement_events"]
        )

        print("\nKnown anomaly detection results:")

        for anomaly, count in report["detected_anomalies"].items():
            print(f"{anomaly}: {count}")

        print("\nVALIDATION COMPLETED")
        print("=" * 60)

        return report

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

    validate_database(args.db)
