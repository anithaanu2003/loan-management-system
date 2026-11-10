import sqlite3
from pathlib import Path
from datetime import date
import calendar

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"


def add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1

    day = min(
        start_date.day,
        calendar.monthrange(year, month)[1]
    )

    return date(year, month, day)


def generate_repayment_schedules():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        applications = connection.execute("""
            SELECT
                a.application_id,
                a.requested_amount,
                a.requested_term_months,
                a.application_date,
                p.annual_interest_rate
            FROM LoanApplication a
            JOIN LoanProduct p
                ON a.product_id = p.product_id
            JOIN Decision d
                ON a.application_id = d.application_id
            WHERE d.decision_status = 'APPROVED'
            ORDER BY a.application_id
        """).fetchall()

        schedules = []

        for application in applications:
            (application_id, principal, term,
             application_date, annual_rate) = application

            monthly_rate = annual_rate / (12 * 100)

            if monthly_rate == 0:
                emi = principal / term
            else:
                factor = (1 + monthly_rate) ** term
                emi = (
                    principal * monthly_rate * factor
                ) / (factor - 1)

            remaining_principal = principal
            start_date = date.fromisoformat(application_date)

            for installment in range(1, term + 1):
                interest = round(
                    remaining_principal * monthly_rate, 2
                )

                if installment == term:
                    principal_payment = remaining_principal
                else:
                    principal_payment = round(emi - interest, 2)

                total_payment = round(
                    principal_payment + interest, 2
                )

                remaining_principal = round(
                    remaining_principal - principal_payment, 2
                )

                due_date = add_months(start_date, installment)

                schedule_id = (
                    f"SCH-{application_id}-{installment:03d}"
                )

                schedules.append((
                    schedule_id,
                    application_id,
                    installment,
                    due_date.isoformat(),
                    principal_payment,
                    interest,
                    total_payment,
                    max(remaining_principal, 0),
                    "PENDING"
                ))

        connection.executemany("""
            INSERT OR IGNORE INTO RepaymentSchedule (
                schedule_id,
                application_id,
                installment_number,
                due_date,
                principal_amount,
                interest_amount,
                total_payment,
                outstanding_balance,
                payment_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, schedules)

        connection.commit()

        total = connection.execute("""
            SELECT COUNT(*) FROM RepaymentSchedule
        """).fetchone()[0]

        print(f"Repayment schedule records created: {total}")
        print(f"Approved applications processed: {len(applications)}")

    finally:
        connection.close()


if __name__ == "__main__":
    generate_repayment_schedules()