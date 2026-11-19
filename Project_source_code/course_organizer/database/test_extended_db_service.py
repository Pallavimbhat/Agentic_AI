"""Tests for extended Course Organizer database operations."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from course_organizer.database.db_service import DatabaseService
from course_organizer.database.init_db import SCHEMA_PATH


class TestExtendedDatabaseService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "extended_test.db"

        connection = sqlite3.connect(str(self.database_path))
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()

        self.db = DatabaseService(self.database_path)

        self.professor = self.db.create_user(
            "Professor Example", "professor@example.edu", "professor"
        )
        self.student = self.db.create_user(
            "Student Example", "student@example.edu", "student"
        )
        self.course = self.db.create_course(
            "CS701", "Computer Vision", 7, created_by=self.professor["id"]
        )
        self.assignment = self.db.create_assignment(
            self.course["id"],
            "Image Classification",
            "2099-12-31",
            max_marks=100,
            created_by=self.professor["id"],
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_note_and_add_version(self):
        note = self.db.create_note(
            self.course["id"], "CNN Notes", "Version one",
            created_by=self.professor["id"],
        )
        self.assertEqual(note["current_version"], 1)
        self.assertEqual(note["latest_version"]["content"], "Version one")

        updated = self.db.add_note_version(
            note["id"], "Version two", created_by=self.professor["id"]
        )
        self.assertEqual(updated["current_version"], 2)
        self.assertEqual(updated["latest_version"]["content"], "Version two")
        self.assertEqual(len(self.db.get_note_versions(note["id"])), 2)

    def test_enroll_student(self):
        enrollment = self.db.enroll_student(
            self.course["id"], self.student["id"]
        )
        self.assertEqual(enrollment["course_id"], self.course["id"])
        students = self.db.list_course_students(self.course["id"])
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["id"], self.student["id"])

    def test_submit_assignment(self):
        submission = self.db.submit_assignment(
            self.assignment["id"],
            self.student["id"],
            content="My assignment answer",
            submitted_at="2099-01-01T12:00:00",
        )
        self.assertEqual(submission["status"], "submitted")
        self.assertEqual(submission["student_id"], self.student["id"])

    def test_late_submission(self):
        submission = self.db.submit_assignment(
            self.assignment["id"],
            self.student["id"],
            content="Late answer",
            submitted_at="2100-01-01T12:00:00",
        )
        self.assertEqual(submission["status"], "late")

    def test_similarity_report_and_review(self):
        submission = self.db.submit_assignment(
            self.assignment["id"], self.student["id"], content="Answer"
        )
        report = self.db.create_similarity_report(
            submission["id"], 82.5, details="High overlap; review required"
        )
        self.assertEqual(report["similarity_score"], 82.5)

        reviewed = self.db.review_similarity_report(
            report["id"], self.professor["id"]
        )
        self.assertEqual(reviewed["reviewed_by"], self.professor["id"])

    def test_grade_approval_and_publication(self):
        submission = self.db.submit_assignment(
            self.assignment["id"], self.student["id"], content="Answer"
        )
        grade = self.db.create_or_update_grade(
            submission["id"], 85, "Good work", graded_by=self.professor["id"]
        )
        self.assertEqual(grade["status"], "draft")

        approved = self.db.approve_grade(grade["id"], self.professor["id"])
        self.assertEqual(approved["status"], "approved")

        published = self.db.publish_grade(grade["id"])
        self.assertEqual(published["status"], "published")
        self.assertIsNotNone(published["published_at"])

    def test_cannot_publish_draft_grade(self):
        submission = self.db.submit_assignment(
            self.assignment["id"], self.student["id"], content="Answer"
        )
        grade = self.db.create_or_update_grade(submission["id"], 70)
        with self.assertRaises(ValueError):
            self.db.publish_grade(grade["id"])

    def test_marks_cannot_exceed_maximum(self):
        submission = self.db.submit_assignment(
            self.assignment["id"], self.student["id"], content="Answer"
        )
        with self.assertRaises(ValueError):
            self.db.create_or_update_grade(submission["id"], 101)

    def test_audit_log(self):
        log = self.db.log_action(
            actor_type="agent",
            action="create_note",
            entity_type="note",
            entity_id=1,
            outcome="success",
            agent_name="Notes Repository Agent",
            details={"test": True},
        )
        self.assertEqual(log["outcome"], "success")
        self.assertIn('"test": true', log["details"])
        self.assertEqual(len(self.db.list_audit_logs(entity_type="note")), 1)

    def test_dashboard_counts_all_tables(self):
        summary = self.db.dashboard_summary()
        for table in (
            "users", "courses", "course_enrollments", "notes", "note_versions",
            "assignments", "submissions", "similarity_reports", "grades",
            "project_milestones", "audit_logs",
        ):
            self.assertIn(table, summary)
        self.assertEqual(summary["users"], 2)
        self.assertEqual(summary["courses"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
