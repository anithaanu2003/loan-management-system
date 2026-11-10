import sqlite3
import json
import argparse
from pathlib import Path
from datetime import date, timedelta

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def make_decision(application):

    (
        application_id,
        monthly_income,
        existing_emi,
        proposed_emi,
        dti,
        affordability_status,
        income_proof,
        employment_status,
        credit_score,
        verified_documents
    ) = application

    total_emi = existing_emi + proposed_emi

    # Rule 1: High debt burden or very low credit score
    if affordability_status == "FAIL" or credit_score < 580:
        return "REJECTED", "High debt burden or low credit score"

    # Rule 2: Missing or unverified documents
    if income_proof != "VERIFIED" or verified_documents < 4:
        return "MANUAL_REVIEW", "Documents require verification"

    # Rule 3: Unstable employment
    if employment_status != "ACTIVE":
        return "MANUAL_REVIEW", "Employment requires review"

    # Rule 4: Borderline affordability or credit score
    if affordability_status == "REVIEW" or credit_score < 650:
        return "MANUAL_REVIEW", "Borderline risk assessment"

    # Rule 5: All checks satisfied
    return "APPROVED", "Affordability and risk checks passed"


def generate_decisions():

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        applications = connection.execute("""
            SELECT
                a.application_id,
                ac.monthly_income,
                ac.existing_monthly_emi,
                ac.proposed_monthly_emi,
                ac.debt_to_income_ratio,
                ac.affordability_status,
                i.proof_status,
                e.employment_status,
                COALESCE(MAX(cf.credit_score), 650),
                (
                    SELECT COUNT(*)
                    FROM Document d
                    WHERE d.application_id = a.application_id
                    AND d.document_status = 'VERIFIED'
                )
            FROM LoanApplication a

            JOIN AffordabilityCheck ac
                ON a.application_id = ac.application_id

            JOIN IncomeRecord i
                ON a.applicant_id = i.applicant_id

            JOIN Employment e
                ON a.applicant_id = e.applicant_id

            LEFT JOIN CreditFacility cf
                ON a.applicant_id = cf.applicant_id

            GROUP BY a.application_id
            ORDER BY a.application_id
        """).fetchall()

        decisions = []
        events = []
        updates = []

        for application in applications:

            (
                application_id,
                monthly_income,
                existing_emi,
                proposed_emi,
                dti,
                affordability_status,
                income_proof,
                employment_status,
                credit_score,
                verified_documents
            ) = application

            decision_status, reason = make_decision(application)

            decision_id = f"DEC-{application_id}-01"

            # Store the inputs used for the decision
            rule_inputs = json.dumps({
                "monthly_income": monthly_income,
                "existing_monthly_emi": existing_emi,
                "proposed_monthly_emi": proposed_emi,
                "debt_to_income_ratio": dti,
                "affordability_status": affordability_status,
                "income_proof": income_proof,
                "employment_status": employment_status,
                "credit_score": credit_score,
                "verified_documents": verified_documents
            })

            checked_at = connection.execute("""
                SELECT checked_at
                FROM AffordabilityCheck
                WHERE application_id = ?
            """, (application_id,)).fetchone()[0]

            decision_date = (
                date.fromisoformat(checked_at[:10])
                + timedelta(days=1)
            )

            decided_at = f"{decision_date.isoformat()}T12:00:00"

            decisions.append((
                decision_id,
                application_id,
                decision_status,
                reason,
                rule_inputs,
                decided_at
            ))

            updates.append((
                decision_status,
                application_id
            ))

            events.append((
                application_id,
                "SUBMITTED",
                decision_status,
                decided_at,
                reason
            ))

        connection.executemany("""
            INSERT OR IGNORE INTO Decision (
                decision_id,
                application_id,
                decision_status,
                decision_reason,
                rule_inputs,
                decided_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, decisions)

        connection.executemany("""
            UPDATE LoanApplication
            SET application_status = ?
            WHERE application_id = ?
        """, updates)

        connection.executemany("""
            INSERT INTO ApplicationEvent (
                application_id,
                previous_status,
                new_status,
                event_timestamp,
                event_reason
            )
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1 FROM ApplicationEvent
                WHERE application_id = ?
            )
        """, [
            event + (event[0],)
            for event in events
        ])

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM Decision"
        ).fetchone()[0]

        print(f"Decisions generated: {total}")

        summary = connection.execute("""
            SELECT decision_status, COUNT(*)
            FROM Decision
            GROUP BY decision_status
            ORDER BY decision_status
        """).fetchall()

        print("\nDecision summary:")

        for status, count in summary:
            print(f"{status}: {count}")

    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate loan application decisions"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite database"
    )

    args = parser.parse_args()

    DB_PATH = Path(args.db).resolve()

    generate_decisions()