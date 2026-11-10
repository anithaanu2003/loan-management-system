
import sqlite3
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def check_disbursement_eligibility(connection, application_id):

    application = connection.execute("""
        SELECT
            a.application_status,
            a.requested_amount,
            a.requested_term_months,
            d.decision_status,
            ac.affordability_status
        FROM LoanApplication a
        LEFT JOIN Decision d
            ON a.application_id = d.application_id
        LEFT JOIN AffordabilityCheck ac
            ON a.application_id = ac.application_id
        WHERE a.application_id = ?
        ORDER BY d.decided_at DESC, ac.checked_at DESC
        LIMIT 1
    """, (application_id,)).fetchone()

    if application is None:
        return False, "Application not found"

    # Check duplicate disbursement FIRST.
    previous_disbursement = connection.execute("""
        SELECT COUNT(*)
        FROM DisbursementEvent
        WHERE application_id = ?
          AND disbursement_status = 'SUCCESS'
    """, (application_id,)).fetchone()[0]

    if previous_disbursement > 0:
        return False, "Successful disbursement already exists"

    (
        application_status,
        requested_amount,
        requested_term,
        decision_status,
        affordability_status
    ) = application

    if application_status != "APPROVED":
        return False, "Application is not approved"

    if decision_status != "APPROVED":
        return False, "Approved decision not found"

    if affordability_status != "PASS":
        return False, "Affordability check has not passed"

    # Check all four required documents.
    documents = connection.execute("""
        SELECT
            COUNT(*),
            SUM(
                CASE WHEN document_status = 'VERIFIED'
                THEN 1 ELSE 0 END
            )
        FROM Document
        WHERE application_id = ?
    """, (application_id,)).fetchone()

    total_documents = documents[0] or 0
    verified_documents = documents[1] or 0

    if total_documents != 4 or verified_documents != 4:
        return False, "All four required documents must be verified"

    # Check repayment schedule completeness.
    schedule = connection.execute("""
        SELECT
            COUNT(*),
            MIN(installment_number),
            MAX(installment_number)
        FROM RepaymentSchedule
        WHERE application_id = ?
    """, (application_id,)).fetchone()

    schedule_count, first_installment, last_installment = schedule

    if (
        schedule_count != requested_term
        or first_installment != 1
        or last_installment != requested_term
    ):
        return False, "Repayment schedule is incomplete"

    return True, "Application is eligible for disbursement"


def record_disbursement(connection, application_id, transaction_reference):

    try:
        connection.execute("BEGIN IMMEDIATE")

        eligible, reason = check_disbursement_eligibility(
            connection, application_id
        )

        if not eligible:
            connection.rollback()
            return False, reason

        amount = connection.execute("""
            SELECT requested_amount
            FROM LoanApplication
            WHERE application_id = ?
        """, (application_id,)).fetchone()[0]

        disbursement_id = f"DISB-{application_id}-01"

        connection.execute("""
            INSERT INTO DisbursementEvent (
                disbursement_id,
                application_id,
                disbursed_amount,
                disbursement_status,
                disbursed_at,
                transaction_reference
            )
            VALUES (?, ?, ?, 'SUCCESS', datetime('now'), ?)
        """, (
            disbursement_id,
            application_id,
            amount,
            transaction_reference
        ))

        connection.execute("""
            UPDATE LoanApplication
            SET application_status = 'DISBURSED'
            WHERE application_id = ?
              AND application_status = 'APPROVED'
        """, (application_id,))

        connection.execute("""
            INSERT INTO ApplicationEvent (
                application_id,
                previous_status,
                new_status,
                event_timestamp,
                event_reason
            )
            VALUES (
                ?, 'APPROVED', 'DISBURSED',
                datetime('now'),
                'Loan successfully disbursed'
            )
        """, (application_id,))

        connection.commit()

        return True, "Loan successfully disbursed"

    except Exception:
        connection.rollback()
        raise


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Loan disbursement management"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite database"
    )

    parser.add_argument(
        "--application-id",
        required=True,
        help="Loan application ID"
    )

    parser.add_argument(
        "--action",
        choices=["check", "disburse"],
        required=True,
        help="Check eligibility or record disbursement"
    )

    parser.add_argument(
        "--transaction-reference",
        help="Transaction reference for disbursement"
    )

    args = parser.parse_args()

    connection = sqlite3.connect(args.db)

    try:
        if args.action == "check":

            eligible, message = check_disbursement_eligibility(
                connection,
                args.application_id
            )

            print("Eligible:", eligible)
            print("Message:", message)

        elif args.action == "disburse":

            if not args.transaction_reference:
                parser.error(
                    "--transaction-reference is required for disbursement"
                )

            success, message = record_disbursement(
                connection,
                args.application_id,
                args.transaction_reference
            )

            print("Success:", success)
            print("Message:", message)

    finally:
        connection.close()