import sqlite3
from datetime import datetime, timezone

from app.database.connection import get_connection


class GradingService:

    @staticmethod
    def grade_submission(
        submission_id,
        professor_id,
        final_marks,
        professor_feedback,
        suggested_marks=None,
        ai_feedback=None
    ):
        connection = get_connection()

        try:
            submission = connection.execute("""
                SELECT s.id, s.student_id, a.maximum_marks
                FROM submissions s
                JOIN assignments a ON a.id = s.assignment_id
                WHERE s.id = ? AND a.created_by = ?
            """, (submission_id, professor_id)).fetchone()

            if not submission:
                raise ValueError(
                    "Submission not found or you do not own its assignment."
                )

            maximum_marks = submission["maximum_marks"]

            if final_marks < 0 or final_marks > maximum_marks:
                raise ValueError(
                    f"Marks must be between 0 and {maximum_marks}."
                )

            if suggested_marks is not None:
                if suggested_marks < 0 or suggested_marks > maximum_marks:
                    raise ValueError("Suggested marks are outside the allowed range.")

            if not professor_feedback or not professor_feedback.strip():
                raise ValueError("Professor feedback cannot be empty.")

            connection.execute("""
                INSERT INTO grades (
                    submission_id,
                    suggested_marks,
                    final_marks,
                    maximum_marks,
                    ai_feedback,
                    professor_feedback,
                    status,
                    graded_by
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)

                ON CONFLICT(submission_id)
                DO UPDATE SET
                    suggested_marks = excluded.suggested_marks,
                    final_marks = excluded.final_marks,
                    maximum_marks = excluded.maximum_marks,
                    ai_feedback = excluded.ai_feedback,
                    professor_feedback = excluded.professor_feedback,
                    status = 'pending',
                    graded_by = excluded.graded_by,
                    approved_at = NULL,
                    published_at = NULL
            """, (
                submission_id,
                suggested_marks,
                final_marks,
                maximum_marks,
                ai_feedback,
                professor_feedback,
                professor_id
            ))

            grade = connection.execute("""
                SELECT id FROM grades WHERE submission_id = ?
            """, (submission_id,)).fetchone()

            connection.execute("""
                INSERT INTO feedback (
                    grade_id,
                    professor_id,
                    student_id,
                    comments
                )
                VALUES (?, ?, ?, ?)
            """, (
                grade["id"],
                professor_id,
                submission["student_id"],
                professor_feedback
            ))

            connection.commit()

            return {
                "success": True,
                "grade_id": grade["id"],
                "submission_id": submission_id,
                "final_marks": final_marks,
                "maximum_marks": maximum_marks,
                "status": "pending"
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def approve_grade(grade_id, professor_id):
        connection = get_connection()

        try:
            result = connection.execute("""
                UPDATE grades
                SET status = 'approved',
                    approved_at = ?
                WHERE id = ?
                  AND graded_by = ?
                  AND status = 'pending'
            """, (
                datetime.now(timezone.utc).isoformat(),
                grade_id,
                professor_id
            ))

            if result.rowcount == 0:
                raise ValueError(
                    "Grade not found, not owned by professor, or not pending."
                )

            connection.commit()

            return {
                "success": True,
                "grade_id": grade_id,
                "status": "approved"
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def publish_grade(grade_id, professor_id):
        connection = get_connection()

        try:
            result = connection.execute("""
                UPDATE grades
                SET status = 'published',
                    published_at = ?
                WHERE id = ?
                  AND graded_by = ?
                  AND status = 'approved'
            """, (
                datetime.now(timezone.utc).isoformat(),
                grade_id,
                professor_id
            ))

            if result.rowcount == 0:
                raise ValueError(
                    "Only an approved grade belonging to you can be published."
                )

            connection.commit()

            return {
                "success": True,
                "grade_id": grade_id,
                "status": "published"
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def get_student_grades(student_id):
        connection = get_connection()

        try:
            rows = connection.execute("""
                SELECT
                    g.id AS grade_id,
                    g.submission_id,
                    g.final_marks,
                    g.maximum_marks,
                    g.professor_feedback,
                    g.status,
                    a.title AS assignment_title,
                    c.course_name
                FROM grades g
                JOIN submissions s ON s.id = g.submission_id
                JOIN assignments a ON a.id = s.assignment_id
                JOIN courses c ON c.id = a.course_id
                WHERE s.student_id = ?
                  AND g.status = 'published'
                ORDER BY g.id DESC
            """, (student_id,)).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()