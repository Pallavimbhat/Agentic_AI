
"""Initialize the Course Organizer SQLite database."""

import sqlite3
from pathlib import Path

DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "course_organizer.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"


def initialize_database():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Database schema not found: {SCHEMA_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        connection.commit()

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        print("Database initialized successfully.")
        print(f"Database location: {DATABASE_PATH}")
        print("\nCreated tables:")

        for (table_name,) in tables:
            print(f"- {table_name}")

        print(f"\nTotal tables: {len(tables)}")

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()

