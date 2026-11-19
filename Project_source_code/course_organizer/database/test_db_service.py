"""Tests for the Course Organizer database service."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from course_organizer.database.db_service import DatabaseService
from course_organizer.database.init_db import SCHEMA_PATH


class TestDatabaseService(unittest.TestCase):

    def setUp(self):
        """Create a fresh temporary database for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"

        # Create the database and initialize all tables.
        connection = sqlite3.connect(str(self.database_path))

        try:
            connection.execute("PRAGMA foreign_keys = ON")
            schema = SCHEMA_PATH.read_text(encoding="utf-8")
            connection.executescript(schema)
            connection.commit()
        finally:
            connection.close()

        # Every DatabaseService connection will use the same database file.
        self.db = DatabaseService(self.database_path)

    def tearDown(self):
        """Clean up the temporary database after each test."""
        self.temp_dir.cleanup()

    def test_create_and_list_course(self):
        course = self.db.create_course(
            "CS701",
            "Computer Vision",
            7,
            "Computer Vision course",
        )

        self.assertEqual(course["name"], "Computer Vision")
        self.assertEqual(len(self.db.list_courses()), 1)

    def test_search_course(self):
        self.db.create_course("CS701", "Computer Vision", 7)

        results = self.db.list_courses(search="Vision")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["course_code"], "CS701")

    def test_update_course(self):
        course = self.db.create_course(
            "CS701",
            "Computer Vision",
            7,
        )

        updated = self.db.update_course(
            course["id"],
            name="Advanced Computer Vision",
        )

        self.assertEqual(
            updated["name"],
            "Advanced Computer Vision",
        )

    def test_delete_course(self):
        course = self.db.create_course(
            "CS701",
            "Computer Vision",
            7,
        )

        result = self.db.delete_course(course["id"])

        self.assertTrue(result["deleted"])
        self.assertEqual(self.db.list_courses(), [])

    def test_invalid_semester(self):
        with self.assertRaises(ValueError):
            self.db.create_course(
                "CS701",
                "Computer Vision",
                13,
            )

    def test_dashboard_summary(self):
        summary = self.db.dashboard_summary()

        self.assertEqual(summary["courses"], 0)
        self.assertEqual(summary["assignments"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)