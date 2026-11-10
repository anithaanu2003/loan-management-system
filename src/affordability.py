import sqlite3
import math
from pathlib import Path
from datetime import date

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def calculate_emi(principal, annual_rate, months):
    monthly_rate = annual_rate / (12 * 100)

    if monthly_rate == 0:
        return principal / months

    factor = (1 + monthly_rate) ** months

    emi = (
        principal * monthly_rate * factor
    ) / (factor - 1)

    return round(emi, 2)


def generate_affordability_checks():

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    applications = connection.execute("""
        SELECT
            a.application_id,
            a.application_date,
            a.requested_amount,
            a.requested_term_months,
            i.monthly_income,
            p.annual_interest_rate
        FROM LoanApplication a
        JOIN IncomeRecord i
            ON a.applicant_id = i.applicant_id
        JOIN LoanProduct p
            ON a.product_id = p.product_id
        ORDER BY a.application_id
    """).fetchall()

    checks = []

    try:
        for application in applications:

            (
                application_id,
                application_date,
                loan_amount,
                loan_term,
                monthly_income,
                annual_rate
            ) = application

            # Calculate existing monthly EMI
            existing_emi = connection.execute("""
                SELECT COALESCE(SUM(monthly_emi), 0)
                FROM CreditFacility
                WHERE applicant_id = (
                    SELECT applicant_id
                    FROM LoanApplication
                    WHERE application_id = ?
                )
                AND facility_status = 'ACTIVE'
            """, (application_id,)).fetchone()[0]

            # Calculate proposed EMI
            proposed_emi = calculate_emi(
                loan_amount,
                annual_rate,
                loan_term
            )

            # Calculate debt-to-income ratio
            total_emi = existing_emi + proposed_emi

            dti = (total_emi / monthly_income) * 100

            # Calculate disposable income
            disposable_income = monthly_income - total_emi

            # Determine affordability status
            if dti <= 40 and disposable_income >= 0:
                status = "PASS"

            elif dti <= 50 and disposable_income >= 0:
                status = "REVIEW"

            else:
                status = "FAIL"

            check_id = f"CHK-{application_id}"

            checked_at = f"{application_date}T12:00:00"

            checks.append((
                check_id,
                application_id,
                monthly_income,
                existing_emi,
                proposed_emi,
                round(dti, 2),
                round(disposable_income, 2),
                status,
                checked_at
            ))

        connection.executemany("""
            INSERT OR IGNORE INTO AffordabilityCheck (
                check_id,
                application_id,
                monthly_income,
                existing_monthly_emi,
                proposed_monthly_emi,
                debt_to_income_ratio,
                disposable_income,
                affordability_status,
                checked_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, checks)

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM AffordabilityCheck"
        ).fetchone()[0]

        print(f"Affordability checks created: {total}")

        summary = connection.execute("""
            SELECT affordability_status, COUNT(*)
            FROM AffordabilityCheck
            GROUP BY affordability_status
            ORDER BY affordability_status
        """).fetchall()

        print("\nAffordability summary:")

        for status, count in summary:
            print(f"{status}: {count}")

    finally:
        connection.close()


if __name__ == "__main__":
    generate_affordability_checks()