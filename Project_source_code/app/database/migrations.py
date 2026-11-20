from app.database.connection import get_connection


def migrate_similarity_reports():
    connection = get_connection()

    try:
        columns = connection.execute(
            "PRAGMA table_info(similarity_reports)"
        ).fetchall()

        existing_columns = [column["name"] for column in columns]

        if "review_decision" not in existing_columns:
            connection.execute("""
                ALTER TABLE similarity_reports
                ADD COLUMN review_decision TEXT
                CHECK (
                    review_decision IS NULL
                    OR review_decision IN ('confirmed', 'not_confirmed')
                )
            """)

            print("Added review_decision column.")

        else:
            print("review_decision column already exists.")

        connection.commit()
        print("Database migration completed successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    migrate_similarity_reports()