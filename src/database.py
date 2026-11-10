from pathlib import Path
import sqlite3

# Find the project folder
ROOT_DIR = Path(__file__).resolve().parents[1]

# Database and schema file locations
DB_PATH = ROOT_DIR / "data" / "loan_management.db"
SCHEMA_PATH = ROOT_DIR / "schema.sql"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with get_connection() as connection:
        connection.executescript(schema)

    print("Database created successfully!")


def main():
    initialize_database()

    with get_connection() as connection:
        tables = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

    print("\nTables created:")
    for table in tables:
        print("-", table[0])

    print(f"\nTotal tables: {len(tables)}")


if __name__ == "__main__":
    main()