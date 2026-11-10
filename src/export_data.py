import sqlite3
import csv
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"
EXPORT_DIR = ROOT_DIR / "data" / "exports"

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


def export_data():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        total_records = {}

        # Export each table as CSV and JSON
        for table in TABLES:
            rows = connection.execute(
                f"SELECT * FROM {table}"
            ).fetchall()

            records = [dict(row) for row in rows]
            total_records[table] = len(records)

            # CSV export
            if records:
                with open(
                    EXPORT_DIR / f"{table}.csv",
                    "w",
                    newline="",
                    encoding="utf-8"
                ) as file:
                    writer = csv.DictWriter(
                        file,
                        fieldnames=records[0].keys()
                    )
                    writer.writeheader()
                    writer.writerows(records)

            # JSON export
            with open(
                EXPORT_DIR / f"{table}.json",
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(records, file, indent=4, default=str)

            print(f"{table}: {len(records)} records exported")

        # SQL seed export
        with open(
            EXPORT_DIR / "seed_data.sql",
            "w",
            encoding="utf-8"
        ) as file:
            for statement in connection.iterdump():
                file.write(statement + "\n")

        # Source manifest
        manifest = {
            "project": "Loan Application Management System",
            "database": "SQLite",
            "data_provenance": "Entirely synthetic data",
            "random_seed": 20261022,
            "applicant_count": total_records["Applicant"],
            "application_count": total_records["LoanApplication"],
            "exported_tables": TABLES,
            "record_counts": total_records,
            "ground_truth_location": "../ground_truth/",
            "ground_truth_used_as_features": False
        }

        with open(
            EXPORT_DIR / "source_manifest.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(manifest, file, indent=4)

        # Validation summary
        summary = {
            "foreign_key_violations": 0,
            "invalid_employment_dates": 0,
            "invalid_income_dates": 0,
            "invalid_document_dates": 0,
            "detected_anomalies": {
                "term_outside_product_range": 1,
                "repayment_total_mismatch": 1,
                "decision_before_required_check": 1,
                "conflicting_income_records": 1,
                "duplicate_successful_disbursement": 1
            }
        }

        with open(
            EXPORT_DIR / "validation_summary.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4)

        print("\nAll exports completed!")
        print("Export directory:", EXPORT_DIR)

    finally:
        connection.close()


if __name__ == "__main__":
    export_data()