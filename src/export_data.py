
import sqlite3
import csv
import json
import argparse
from pathlib import Path

if __package__:
    from .validation import validate_database
else:
    from validation import validate_database


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


def export_data(db_path=None, export_dir=None, ground_truth_location=None):

    target_db = Path(db_path).resolve() if db_path else DB_PATH
    target_export_dir = (
        Path(export_dir).resolve() if export_dir else EXPORT_DIR
    )

    target_export_dir.mkdir(parents=True, exist_ok=True)

    if not target_db.exists():
        raise FileNotFoundError(f"Database not found: {target_db}")

    # Validate the exact database being exported.
    validation_report = validate_database(target_db)

    connection = sqlite3.connect(target_db)
    connection.row_factory = sqlite3.Row

    try:
        total_records = {}

        # Export each table as CSV and JSON.
        for table in TABLES:
            rows = connection.execute(
                f"SELECT * FROM {table}"
            ).fetchall()

            records = [dict(row) for row in rows]
            total_records[table] = len(records)

            # Get column names from the database schema.
            columns = [
                column["name"]
                for column in connection.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
            ]

            # CSV export, including headers for empty tables.
            with open(
                target_export_dir / f"{table}.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.DictWriter(
                    file,
                    fieldnames=columns
                )
                writer.writeheader()

                if records:
                    writer.writerows(records)

            # JSON export.
            with open(
                target_export_dir / f"{table}.json",
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(records, file, indent=4, default=str)

            print(f"{table}: {len(records)} records exported")

        # SQL seed export.
        with open(
            target_export_dir / "seed_data.sql",
            "w",
            encoding="utf-8"
        ) as file:

            for statement in connection.iterdump():
                file.write(statement + "\n")

        # Source manifest.
        manifest = {
            "project": "Loan Application Management System",
            "database": "SQLite",
            "data_provenance": "Entirely synthetic data",
            "random_seed": 20261022,
            "source_database": target_db.name,
            "applicant_count": total_records["Applicant"],
            "application_count": total_records["LoanApplication"],
            "exported_tables": TABLES,
            "record_counts": total_records,
            "ground_truth_location": (
                Path(ground_truth_location).name
                if ground_truth_location
                else None
            ),
            "ground_truth_used_as_features": False
        }

        with open(
            target_export_dir / "source_manifest.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(manifest, file, indent=4)

        # Dynamic validation summary.
        summary = {
            "database": Path(validation_report["database"]).name,
            "record_counts": validation_report["record_counts"],
            "foreign_key_violations": validation_report[
                "foreign_key_violations"
            ],
            "date_validation": validation_report["date_validation"],
            "lifecycle_inconsistencies": validation_report[
                "lifecycle_inconsistencies"
            ],
            "disbursement_status_inconsistencies": validation_report[
                "disbursement_status_inconsistencies"
            ],
            "missing_successful_disbursement_events": validation_report[
                "missing_successful_disbursement_events"
            ],
            "detected_anomalies": validation_report["detected_anomalies"]
        }

        with open(
            target_export_dir / "validation_summary.json",
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(summary, file, indent=4)

        print("\nAll exports completed!")
        print("Export directory:", target_export_dir)

    finally:
        connection.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Export loan management database"
    )

    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to the SQLite database"
    )

    parser.add_argument(
        "--export-dir",
        type=str,
        default=str(EXPORT_DIR),
        help="Path to the export directory"
    )

    parser.add_argument(
        "--ground-truth-location",
        type=str,
        default=None,
        help="Location of the corresponding ground-truth files"
    )

    args = parser.parse_args()

    export_data(
        db_path=args.db,
        export_dir=args.export_dir,
        ground_truth_location=args.ground_truth_location
    )
