import sqlite3
import csv
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"
GROUND_TRUTH_DIR = ROOT_DIR / "ground_truth"

def inject_anomalies():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    anomalies = []

    try:
        # 1. Loan term outside product range
        application = connection.execute("""
            SELECT a.application_id, p.max_term_months
            FROM LoanApplication a
            JOIN LoanProduct p ON a.product_id = p.product_id
            WHERE a.requested_term_months = p.max_term_months
            LIMIT 1
        """).fetchone()

        if application is None:
            application = connection.execute("""
                SELECT a.application_id, p.max_term_months
                FROM LoanApplication a
                JOIN LoanProduct p ON a.product_id = p.product_id
                LIMIT 1
            """).fetchone()

        app_id, max_term = application

        connection.execute("""
            UPDATE LoanApplication
            SET requested_term_months = ?
            WHERE application_id = ?
        """, (max_term + 1, app_id))

        anomalies.append({
            "anomaly_id": "ANOM-001",
            "anomaly_type": "TERM_OUTSIDE_PRODUCT_RANGE",
            "application_id": app_id,
            "description": "Requested loan term exceeds product maximum"
        })

        # 2. Repayment schedule does not reconcile
        schedule = connection.execute("""
            SELECT schedule_id, application_id
            FROM RepaymentSchedule
            LIMIT 1
        """).fetchone()

        if schedule:
            schedule_id, app_id = schedule

            connection.execute("""
                UPDATE RepaymentSchedule
                SET total_payment = total_payment + 100
                WHERE schedule_id = ?
            """, (schedule_id,))

            anomalies.append({
                "anomaly_id": "ANOM-002",
                "anomaly_type": "REPAYMENT_TOTAL_MISMATCH",
                "application_id": app_id,
                "record_id": schedule_id,
                "description": "Total payment does not equal principal plus interest"
            })

        # 3. Decision made before affordability check
        decision = connection.execute("""
            SELECT d.decision_id, d.application_id
            FROM Decision d
            JOIN AffordabilityCheck ac
                ON d.application_id = ac.application_id
            LIMIT 1
        """).fetchone()

        if decision:
            decision_id, app_id = decision

            connection.execute("""
                UPDATE Decision
                SET decided_at = '2020-01-01T00:00:00'
                WHERE decision_id = ?
            """, (decision_id,))

            anomalies.append({
                "anomaly_id": "ANOM-003",
                "anomaly_type": "DECISION_BEFORE_REQUIRED_CHECK",
                "application_id": app_id,
                "record_id": decision_id,
                "description": "Decision timestamp is earlier than affordability check"
            })

        # 4. Conflicting income records
        income = connection.execute("""
            SELECT
                i.applicant_id,
                i.monthly_income,
                i.effective_from
            FROM IncomeRecord i
            JOIN LoanApplication a
                ON i.applicant_id = a.applicant_id
            LIMIT 1
        """).fetchone()

        applicant_id, monthly_income, effective_from = income

        connection.execute("""
            INSERT INTO IncomeRecord (
                income_id, applicant_id, employment_id,
                monthly_income, income_source, proof_status,
                effective_from, effective_to
            )
            VALUES (?, ?, NULL, ?, 'OTHER', 'VERIFIED', ?, NULL)
        """, (
            "INC-CONFLICT-000001",
            applicant_id,
            round(monthly_income * 2, 2),
            effective_from
        ))

        anomalies.append({
            "anomaly_id": "ANOM-004",
            "anomaly_type": "CONFLICTING_INCOME_RECORDS",
            "applicant_id": applicant_id,
            "record_id": "INC-CONFLICT-000001",
            "description": "Two income records report different monthly income for the same applicant"
        })

        # 5. Duplicate successful disbursement
        approved = connection.execute("""
            SELECT a.application_id, a.requested_amount
            FROM LoanApplication a
            JOIN Decision d
                ON a.application_id = d.application_id
            WHERE d.decision_status = 'APPROVED'
            LIMIT 1
        """).fetchone()

        app_id, amount = approved

        connection.executemany("""
            INSERT INTO DisbursementEvent (
                disbursement_id, application_id,
                disbursed_amount, disbursement_status,
                disbursed_at, transaction_reference
            )
            VALUES (?, ?, ?, 'SUCCESS', ?, ?)
        """, [
            (
                "DISB-ANOM-001",
                app_id,
                amount,
                "2026-11-10T10:00:00",
                "TXN-ANOM-001"
            ),
            (
                "DISB-ANOM-002",
                app_id,
                amount,
                "2026-11-10T10:05:00",
                "TXN-ANOM-002"
            )
        ])

        anomalies.append({
            "anomaly_id": "ANOM-005",
            "anomaly_type": "DUPLICATE_DISBURSEMENT",
            "application_id": app_id,
            "description": "Two successful disbursements exist for the same application"
        })
        
        # 6. Duplicate loan applications
        duplicate_applications = connection.execute("""
            SELECT
                applicant_id,
                product_id,
                requested_amount,
                requested_term_months,
                application_date,
                GROUP_CONCAT(application_id) AS application_ids,
                COUNT(*) AS application_count
            FROM LoanApplication
            GROUP BY
                applicant_id,
                product_id,
                requested_amount,
                requested_term_months,
                application_date
            HAVING COUNT(*) > 1
        """).fetchall()

        for duplicate in duplicate_applications:
            (
                applicant_id,
                product_id,
                requested_amount,
                requested_term,
                application_date,
                application_ids,
                application_count
            ) = duplicate

            anomalies.append({
                "anomaly_id": "ANOM-006",
                "anomaly_type": "DUPLICATE_LOAN_APPLICATION",
                "applicant_id": applicant_id,
                "application_ids": application_ids,
                "duplicate_count": application_count,
                "description": (
                    "Same applicant submitted matching loan applications"
                )
            })
        connection.commit()

        # Save ground truth separately
        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

        json_path = GROUND_TRUTH_DIR / "ground_truth.json"

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(anomalies, file, indent=4)

        csv_path = GROUND_TRUTH_DIR / "ground_truth.csv"

        with open(csv_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=sorted({
                    key for anomaly in anomalies
                    for key in anomaly
                })
            )
            writer.writeheader()
            writer.writerows(anomalies)

        print(f"Anomalies injected: {len(anomalies)}")
        print("Ground truth files created:")
        print("-", json_path)
        print("-", csv_path)

        for anomaly in anomalies:
            print(
                anomaly["anomaly_id"],
                anomaly["anomaly_type"]
            )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inject known anomalies into the loan database"
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite database"
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        default=str(GROUND_TRUTH_DIR),
        help="Directory for ground truth files"
    )

    args = parser.parse_args()

    DB_PATH = Path(args.db).resolve()
    GROUND_TRUTH_DIR = Path(args.ground_truth_dir).resolve()

    inject_anomalies()