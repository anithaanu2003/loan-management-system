import sqlite3
import shutil
from pathlib import Path

import pytest

from src.disbursement import (
    check_disbursement_eligibility,
    record_disbursement
)

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT_DIR / "data" / "duplicate_test.db"
APPLICATION_ID = "LOAN-2026-000042"


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "disbursement_test.db"
    shutil.copy2(SOURCE_DB, db_path)

    connection = sqlite3.connect(db_path)

    try:
        yield connection
    finally:
        connection.close()


def test_eligible_application_can_be_disbursed(test_db):
    success, message = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-001"
    )

    assert success is True
    assert message == "Loan successfully disbursed"

    status = test_db.execute(
        """
        SELECT application_status
        FROM LoanApplication
        WHERE application_id = ?
        """,
        (APPLICATION_ID,)
    ).fetchone()[0]

    assert status == "DISBURSED"


def test_duplicate_disbursement_is_blocked(test_db):
    first_success, _ = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-002"
    )

    second_success, message = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-003"
    )

    assert first_success is True
    assert second_success is False
    assert message == "Successful disbursement already exists"

    count = test_db.execute(
        """
        SELECT COUNT(*)
        FROM DisbursementEvent
        WHERE application_id = ?
          AND disbursement_status = 'SUCCESS'
        """,
        (APPLICATION_ID,)
    ).fetchone()[0]

    assert count == 1


def test_rejected_application_cannot_be_disbursed(test_db):
    rejected_application = test_db.execute(
        """
        SELECT application_id
        FROM LoanApplication
        WHERE application_status = 'REJECTED'
        LIMIT 1
        """
    ).fetchone()

    assert rejected_application is not None

    application_id = rejected_application[0]

    success, message = record_disbursement(
        test_db,
        application_id,
        "TXN-AUTOMATED-004"
    )

    assert success is False
    assert message == "Application is not approved"


def test_disbursement_records_event_history(test_db):
    success, _ = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-005"
    )

    assert success is True

    event = test_db.execute(
        """
        SELECT previous_status, new_status, event_reason
        FROM ApplicationEvent
        WHERE application_id = ?
          AND new_status = 'DISBURSED'
        ORDER BY event_timestamp DESC
        LIMIT 1
        """,
        (APPLICATION_ID,)
    ).fetchone()

    assert event == (
        "APPROVED",
        "DISBURSED",
        "Loan successfully disbursed"
    )


def test_nonexistent_application_cannot_be_disbursed(test_db):
    success, message = record_disbursement(
        test_db,
        "LOAN-2026-999999",
        "TXN-AUTOMATED-006"
    )

    assert success is False
    assert message == "Application not found"


def test_failed_affordability_blocks_disbursement(test_db):
    test_db.execute(
        """
        UPDATE AffordabilityCheck
        SET affordability_status = 'FAIL'
        WHERE application_id = ?
        """,
        (APPLICATION_ID,)
    )

    test_db.commit()

    success, message = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-007"
    )

    assert success is False
    assert message == "Affordability check has not passed"


def test_unverified_document_blocks_disbursement(test_db):
    test_db.execute(
        """
        UPDATE Document
        SET document_status = 'REJECTED'
        WHERE rowid = (
            SELECT rowid
            FROM Document
            WHERE application_id = ?
            LIMIT 1
        )
        """,
        (APPLICATION_ID,)
    )

    test_db.commit()

    success, message = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-008"
    )

    assert success is False
    assert message == "All four required documents must be verified"


def test_incomplete_repayment_schedule_blocks_disbursement(test_db):
    test_db.execute(
        """
        DELETE FROM RepaymentSchedule
        WHERE rowid = (
            SELECT rowid
            FROM RepaymentSchedule
            WHERE application_id = ?
            LIMIT 1
        )
        """,
        (APPLICATION_ID,)
    )

    test_db.commit()

    success, message = record_disbursement(
        test_db,
        APPLICATION_ID,
        "TXN-AUTOMATED-009"
    )

    assert success is False
    assert message == "Repayment schedule is incomplete"
