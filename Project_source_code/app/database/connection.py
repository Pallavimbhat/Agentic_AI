import sqlite3
from pathlib import Path


# =====================================================
# PROJECT PATHS
# =====================================================

# Find the main project directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Database directory
DATA_DIR = BASE_DIR / "data"

# Database file
DATABASE_PATH = DATA_DIR / "course_organizer.db"

# SQL schema file
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    """

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    # Enable foreign key constraints
    connection.execute("PRAGMA foreign_keys = ON")

    # Return database rows as dictionary-like objects
    connection.row_factory = sqlite3.Row

    return connection


# =====================================================
# DATABASE INITIALIZATION
# =====================================================

def initialize_database():
    """
    Creates all database tables using schema.sql.
    """

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Database schema not found: {SCHEMA_PATH}"
        )

    connection = get_connection()

    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
            schema = file.read()

        connection.executescript(schema)

        print("\n============================================")
        print("       DATABASE INITIALIZATION")
        print("============================================")

        print("[SUCCESS] SQLite database connected.")
        print("[SUCCESS] Foreign key constraints enabled.")
        print("[SUCCESS] Database schema executed.")

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        print(f"\n[TABLES CREATED] {len(tables)}")

        for table in tables:
            print(f"  [OK] {table['name']}")

        print("\n[DATABASE PATH]")
        print(DATABASE_PATH)

        print("\n============================================")

    except Exception as error:
        print(f"\n[DATABASE ERROR] {error}")
        raise

    finally:
        connection.close()


# =====================================================
# DATABASE TEST
# =====================================================

def test_database_connection():
    """
    Verifies that the database is accessible.
    """

    connection = get_connection()

    try:
        result = connection.execute(
            "SELECT sqlite_version()"
        ).fetchone()

        print(
            f"\n[DATABASE TEST] SQLite version: {result[0]}"
        )

        return True

    except sqlite3.Error as error:
        print(f"[DATABASE TEST FAILED] {error}")
        return False

    finally:
        connection.close()


# =====================================================
# DIRECT EXECUTION
# =====================================================

if __name__ == "__main__":
    initialize_database()
    test_database_connection()