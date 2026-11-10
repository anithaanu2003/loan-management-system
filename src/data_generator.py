import random
import sqlite3
from pathlib import Path
from datetime import date, timedelta

# Project paths
ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "loan_management.db"

# Reproducible random data
SEED = 20261022
TOTAL_APPLICANTS = 10000

random_generator = random.Random(SEED)

# Sample names and cities
FIRST_NAMES = [
    "Aarav", "Ananya", "Rahul", "Priya", "Arjun",
    "Sneha", "Kiran", "Divya", "Rohan", "Pooja",
    "Vijay", "Kavya", "Sai", "Meera", "Varun",
    "Neha", "Aditya", "Sravya", "Nikhil", "Anitha"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Reddy", "Patel", "Rao",
    "Singh", "Gupta", "Verma", "Naidu", "Shah",
    "Mehta", "Das", "Mishra", "Chowdary", "Iyer"
]

CITIES = [
    "Hyderabad", "Bengaluru", "Chennai", "Mumbai",
    "Pune", "Delhi", "Vijayawada", "Visakhapatnam",
    "Kolkata", "Coimbatore"
]


def random_date(start_date, end_date):
    days = (end_date - start_date).days
    random_days = random_generator.randint(0, days)
    return start_date + timedelta(days=random_days)


def generate_applicants():
    applicants = []

    today = date(2026, 11, 10)
    earliest_dob = date(1965, 1, 1)
    latest_dob = date(2005, 1, 1)

    earliest_created = date(2025, 1, 1)

    for number in range(1, TOTAL_APPLICANTS + 1):

        applicant_id = f"APP-2026-{number:06d}"

        first_name = random_generator.choice(FIRST_NAMES)
        last_name = random_generator.choice(LAST_NAMES)

        dob = random_date(earliest_dob, latest_dob)
        created = random_date(earliest_created, today)

        email = f"applicant{number:06d}@example.com"
        phone = str(9000000000 + number)

        city = random_generator.choice(CITIES)

        status = random_generator.choices(
            ["ACTIVE", "INACTIVE"],
            weights=[90, 10]
        )[0]

        applicants.append((
            applicant_id,
            first_name,
            last_name,
            dob.isoformat(),
            email,
            phone,
            city,
            status,
            created.isoformat()
        ))

    return applicants


def insert_applicants():
    applicants = generate_applicants()

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executemany("""
            INSERT OR IGNORE INTO Applicant (
                applicant_id,
                first_name,
                last_name,
                date_of_birth,
                email,
                phone,
                city,
                applicant_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, applicants)

        connection.commit()

        result = connection.execute(
            "SELECT COUNT(*) FROM Applicant"
        ).fetchone()

        print("Applicant data generation completed!")
        print(f"Total applicants in database: {result[0]}")

    finally:
        connection.close()
        
def generate_employment():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    applicants = connection.execute(
        "SELECT applicant_id FROM Applicant"
    ).fetchall()

    employment_records = []

    today = date(2026, 11, 10)

    employers = [
        "TCS", "Infosys", "Wipro", "Accenture",
        "HCL", "Tech Mahindra", "Amazon",
        "Self Business", "Local Company"
    ]

    job_titles = [
        "Software Engineer", "Accountant",
        "Teacher", "Manager", "Analyst",
        "Consultant", "Business Owner",
        "Sales Executive"
    ]

    for number, (applicant_id,) in enumerate(applicants, start=1):

        employment_id = f"EMP-{number:06d}"

        employment_type = random_generator.choice([
            "PERMANENT", "CONTRACT", "SELF_EMPLOYED"
        ])

        start_date = random_date(
            date(2018, 1, 1),
            date(2025, 1, 1)
        )

        employment_status = random_generator.choices(
            ["ACTIVE", "ENDED"],
            weights=[85, 15]
        )[0]

        end_date = None

        if employment_status == "ENDED":
            end_date = random_date(
                start_date,
                today
            ).isoformat()

        annual_salary = round(
            random_generator.uniform(180000, 1800000), 2
        )

        employer = random_generator.choice(employers)
        job_title = random_generator.choice(job_titles)

        employment_records.append((
            employment_id,
            applicant_id,
            employer,
            job_title,
            employment_type,
            start_date.isoformat(),
            end_date,
            employment_status,
            annual_salary
        ))

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO Employment (
                employment_id,
                applicant_id,
                employer_name,
                job_title,
                employment_type,
                start_date,
                end_date,
                employment_status,
                annual_salary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, employment_records)

        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM Employment"
        ).fetchone()[0]

        print(f"Employment records created: {count}")

    finally:
        connection.close()
        
def generate_income_records():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    records = connection.execute("""
        SELECT
            e.employment_id,
            e.applicant_id,
            e.annual_salary,
            e.employment_type,
            e.start_date,
            e.end_date
        FROM Employment e
    """).fetchall()

    income_records = []

    for number, record in enumerate(records, start=1):
        (
            employment_id,
            applicant_id,
            annual_salary,
            employment_type,
            start_date,
            end_date
        ) = record

        income_id = f"INC-{number:06d}"

        # Calculate monthly income from annual salary
        monthly_income = round(annual_salary / 12, 2)

        if employment_type == "SELF_EMPLOYED":
            income_source = "BUSINESS"
        else:
            income_source = "SALARY"

        # Include different income proof situations
        proof_status = random_generator.choices(
            ["VERIFIED", "PENDING", "MISSING", "REJECTED"],
            weights=[70, 12, 10, 8]
        )[0]

        income_records.append((
            income_id,
            applicant_id,
            employment_id,
            monthly_income,
            income_source,
            proof_status,
            start_date,
            end_date
        ))

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO IncomeRecord (
                income_id,
                applicant_id,
                employment_id,
                monthly_income,
                income_source,
                proof_status,
                effective_from,
                effective_to
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, income_records)

        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM IncomeRecord"
        ).fetchone()[0]

        print(f"Income records created: {count}")

        proof_counts = connection.execute("""
            SELECT proof_status, COUNT(*)
            FROM IncomeRecord
            GROUP BY proof_status
            ORDER BY proof_status
        """).fetchall()

        print("\nIncome proof summary:")
        for status, total in proof_counts:
            print(f"{status}: {total}")

    finally:
        connection.close()
    
def generate_credit_facilities():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    applicants = connection.execute(
        "SELECT applicant_id FROM Applicant"
    ).fetchall()

    records = []
    facility_number = 1

    facility_types = [
        "PERSONAL",
        "HOME",
        "AUTO",
        "EDUCATION",
        "CREDIT_CARD"
    ]

    for (applicant_id,) in applicants:

        # Some applicants have no existing credit facilities
        number_of_facilities = random_generator.choices(
            [0, 1, 2, 3],
            weights=[15, 55, 25, 5]
        )[0]

        # One credit score shared by this applicant's facilities
        credit_score = random_generator.randint(300, 900)

        for _ in range(number_of_facilities):

            facility_id = f"FAC-{facility_number:06d}"
            facility_number += 1

            facility_type = random_generator.choice(facility_types)

            facility_status = random_generator.choices(
                ["ACTIVE", "CLOSED"],
                weights=[80, 20]
            )[0]

            if facility_status == "CLOSED":
                outstanding_balance = 0
                monthly_emi = 0
            else:
                outstanding_balance = round(
                    random_generator.uniform(10000, 800000), 2
                )

                monthly_emi = round(
                    random_generator.uniform(1000, 30000), 2
                )

            effective_date = random_date(
                date(2020, 1, 1),
                date(2026, 1, 1)
            )

            records.append((
                facility_id,
                applicant_id,
                facility_type,
                outstanding_balance,
                monthly_emi,
                credit_score,
                facility_status,
                effective_date.isoformat()
            ))

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO CreditFacility (
                facility_id,
                applicant_id,
                facility_type,
                outstanding_balance,
                monthly_emi,
                credit_score,
                facility_status,
                effective_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, records)

        connection.commit()

        count = connection.execute(
            "SELECT COUNT(*) FROM CreditFacility"
        ).fetchone()[0]

        print(f"\nCredit facilities created: {count}")

        summary = connection.execute("""
            SELECT facility_status, COUNT(*)
            FROM CreditFacility
            GROUP BY facility_status
        """).fetchall()

        print("\nCredit facility summary:")
        for status, total in summary:
            print(f"{status}: {total}")

    finally:
        connection.close()
        
def generate_loan_products():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    products = [
        (
            "PROD-001",
            "Personal Loan",
            10000,
            500000,
            12.0,
            6,
            60,
            "ACTIVE"
        ),
        (
            "PROD-002",
            "Home Loan",
            500000,
            5000000,
            8.5,
            60,
            360,
            "ACTIVE"
        ),
        (
            "PROD-003",
            "Vehicle Loan",
            50000,
            1500000,
            10.0,
            12,
            84,
            "ACTIVE"
        ),
        (
            "PROD-004",
            "Education Loan",
            50000,
            2000000,
            9.0,
            12,
            120,
            "ACTIVE"
        )
    ]

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO LoanProduct (
                product_id,
                product_name,
                min_amount,
                max_amount,
                annual_interest_rate,
                min_term_months,
                max_term_months,
                product_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, products)

        connection.commit()

        result = connection.execute("""
            SELECT
                product_id,
                product_name,
                min_amount,
                max_amount,
                min_term_months,
                max_term_months
            FROM LoanProduct
            ORDER BY product_id
        """).fetchall()

        print("\nLoan products created:")

        for product in result:
            print(product)

        print(f"\nTotal loan products: {len(result)}")

    finally:
        connection.close()
        
def generate_loan_applications():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    applicants = [
        row[0] for row in connection.execute(
            "SELECT applicant_id FROM Applicant"
        ).fetchall()
    ]

    products = connection.execute("""
        SELECT
            product_id,
            min_amount,
            max_amount,
            min_term_months,
            max_term_months
        FROM LoanProduct
        WHERE product_status = 'ACTIVE'
    """).fetchall()

    # Select 6,000 different applicants
    selected_applicants = random_generator.sample(
        applicants, 6000
    )

    applications = []

    for number, applicant_id in enumerate(
        selected_applicants, start=1
    ):
        product = random_generator.choice(products)

        (
            product_id,
            min_amount,
            max_amount,
            min_term,
            max_term
        ) = product

        requested_amount = round(
            random_generator.uniform(min_amount, max_amount), 2
        )

        requested_term = random_generator.randint(
            min_term, max_term
        )

        application_date = random_date(
            date(2026, 1, 1),
            date(2026, 11, 10)
        )

        application_id = f"LOAN-2026-{number:06d}"

        applications.append((
            application_id,
            applicant_id,
            product_id,
            requested_amount,
            requested_term,
            application_date.isoformat(),
            "SUBMITTED"
        ))

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO LoanApplication (
                application_id,
                applicant_id,
                product_id,
                requested_amount,
                requested_term_months,
                application_date,
                application_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, applications)

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM LoanApplication"
        ).fetchone()[0]

        print(f"\nLoan applications created: {total}")

        summary = connection.execute("""
            SELECT p.product_name, COUNT(*)
            FROM LoanApplication a
            JOIN LoanProduct p
                ON a.product_id = p.product_id
            GROUP BY p.product_name
            ORDER BY p.product_name
        """).fetchall()

        print("\nApplications by product:")
        for product_name, count in summary:
            print(f"{product_name}: {count}")

    finally:
        connection.close()
        
def generate_documents():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    applications = connection.execute("""
        SELECT
            a.application_id,
            a.applicant_id,
            a.application_date,
            i.proof_status
        FROM LoanApplication a
        JOIN IncomeRecord i
            ON a.applicant_id = i.applicant_id
    """).fetchall()

    documents = []

    document_types = [
        "ID_PROOF",
        "INCOME_PROOF",
        "ADDRESS_PROOF",
        "BANK_STATEMENT"
    ]

    today = date(2026, 11, 10)

    for application_id, applicant_id, app_date, income_status in applications:

        application_date = date.fromisoformat(app_date)

        for number, document_type in enumerate(document_types, start=1):

            document_id = f"DOC-{application_id}-{number:03d}"

            if document_type == "INCOME_PROOF":
                status_mapping = {
                    "VERIFIED": "VERIFIED",
                    "PENDING": "SUBMITTED",
                    "MISSING": "MISSING",
                    "REJECTED": "REJECTED"
                }

                document_status = status_mapping[income_status]

            else:
                document_status = random_generator.choices(
                    ["VERIFIED", "SUBMITTED", "REJECTED", "MISSING"],
                    weights=[75, 12, 8, 5]
                )[0]

            submitted_at = None
            verified_at = None

            if document_status != "MISSING":
                submitted_date = random_date(
                    application_date, today
                )
                submitted_at = submitted_date.isoformat()

            if document_status == "VERIFIED":
                verified_date = random_date(
                    submitted_date, today
                )
                verified_at = verified_date.isoformat()

            documents.append((
                document_id,
                application_id,
                document_type,
                document_status,
                submitted_at,
                verified_at
            ))

    try:
        connection.executemany("""
            INSERT OR IGNORE INTO Document (
                document_id,
                application_id,
                document_type,
                document_status,
                submitted_at,
                verified_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, documents)

        connection.commit()

        total = connection.execute(
            "SELECT COUNT(*) FROM Document"
        ).fetchone()[0]

        print(f"\nDocuments created: {total}")

        summary = connection.execute("""
            SELECT document_status, COUNT(*)
            FROM Document
            GROUP BY document_status
            ORDER BY document_status
        """).fetchall()

        print("\nDocument status summary:")

        for status, count in summary:
            print(f"{status}: {count}")

    finally:
        connection.close()


if __name__ == "__main__":
    insert_applicants()
    generate_employment()
    generate_income_records()
    generate_credit_facilities()
    generate_loan_products()
    generate_loan_applications()
    generate_documents()