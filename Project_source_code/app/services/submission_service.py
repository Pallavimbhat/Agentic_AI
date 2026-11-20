import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

from app.database.connection import get_connection


class SubmissionService:

    @staticmethod
    def calculate_file_hash(file_path):
        """Generate a SHA-256 fingerprint for an uploaded file."""

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            for chunk in iter(lambda: file.read(8192), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    @staticmethod
    def submit_assignment(assignment_id, student_id, file_path):
        """Validate, store and process a student assignment submission."""

        connection = get_connection()

        try:
            # 1. Verify assignment.
            assignment = connection.execute(
                """
                SELECT id, course_id, deadline, status
                FROM assignments
                WHERE id = ?
                """,
                (assignment_id,)
            ).fetchone()

            if not assignment:
                raise ValueError("Assignment not found.")

            if assignment["status"] != "published":
                raise ValueError(
                    "This assignment is not accepting submissions."
                )

            # 2. Verify student enrolment.
            enrollment = connection.execute(
                """
                SELECT id
                FROM enrollments
                WHERE course_id = ? AND student_id = ?
                """,
                (assignment["course_id"], student_id)
            ).fetchone()

            if not enrollment:
                raise ValueError(
                    "You are not enrolled in this course."
                )

            # 3. Calculate SHA-256 hash.
            file_hash = SubmissionService.calculate_file_hash(file_path)

            # 4. Check exact duplicates within this assignment.
            duplicate = connection.execute(
                """
                SELECT id, student_id
                FROM submissions
                WHERE assignment_id = ?
                  AND file_hash = ?
                """,
                (assignment_id, file_hash)
            ).fetchone()

            # 5. Determine initial status.
            deadline = datetime.fromisoformat(assignment["deadline"])

            if duplicate:
                submission_status = "flagged_review"
            elif datetime.now() > deadline:
                submission_status = "late"
            else:
                submission_status = "pending_similarity"

            # 6. Save submission.
            cursor = connection.execute(
                """
                INSERT INTO submissions (
                    assignment_id,
                    student_id,
                    file_path,
                    file_hash,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    assignment_id,
                    student_id,
                    str(file_path),
                    file_hash,
                    submission_status
                )
            )

            submission_id = cursor.lastrowid
            connection.commit()

        except (sqlite3.IntegrityError, ValueError):
            connection.rollback()
            raise

        finally:
            connection.close()

        # 7. Run content-based similarity outside the submission transaction.
        similarity_result = None

        supported_extensions = {
            ".pdf", ".docx", ".pptx", ".txt", ".md"
        }

        extension = Path(file_path).suffix.lower()

        if not duplicate and extension in supported_extensions:
            try:
                from app.services.similarity_service import SimilarityService

                similarity_result = SimilarityService.compare_submission(
                    submission_id,
                    assignment_id
                )

                if similarity_result["flagged_for_review"]:
                    submission_status = "flagged_review"

            except Exception as error:
                # Preserve the submission if similarity processing fails.
                similarity_result = {
                    "success": False,
                    "error": str(error),
                    "message": (
                        "Submission saved, but similarity processing failed."
                    )
                }

        return {
            "submission_id": submission_id,
            "assignment_id": assignment_id,
            "status": submission_status,
            "exact_duplicate_detected": duplicate is not None,
            "duplicate_submission_id": (
                duplicate["id"] if duplicate else None
            ),
            "similarity_check_performed": (
                similarity_result is not None
                and similarity_result.get("success", False)
            ),
            "similarity_result": similarity_result,
            "message": (
                "Exact duplicate detected. Submission flagged for review."
                if duplicate
                else "Submission uploaded and similarity processing completed."
                if similarity_result and similarity_result.get("success")
                else "Submission saved. Similarity processing is pending or failed."
                if extension in supported_extensions
                else "Submission uploaded successfully. Content comparison skipped for this format."
            )
        }

    @staticmethod
    def get_assignment_submissions(assignment_id, professor_id):
        """Allow the course professor to view submissions."""

        connection = get_connection()

        try:
            assignment = connection.execute(
                """
                SELECT id
                FROM assignments
                WHERE id = ? AND created_by = ?
                """,
                (assignment_id, professor_id)
            ).fetchone()

            if not assignment:
                raise ValueError(
                    "Assignment not found or access denied."
                )

            rows = connection.execute(
                """
                SELECT
                    s.id,
                    s.assignment_id,
                    s.student_id,
                    u.full_name AS student_name,
                    s.submitted_at,
                    s.status
                FROM submissions s
                JOIN users u ON u.id = s.student_id
                WHERE s.assignment_id = ?
                ORDER BY s.submitted_at DESC
                """,
                (assignment_id,)
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()