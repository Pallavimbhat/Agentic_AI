import sqlite3
from datetime import datetime

from app.database.connection import get_connection


class AssignmentService:

    @staticmethod
    def create_assignment(
        course_id,
        title,
        description,
        instructions,
        maximum_marks,
        deadline,
        created_by,
        status="published"
    ):
        if maximum_marks <= 0:
            raise ValueError("Maximum marks must be greater than zero.")

        if status not in {"draft", "published", "closed"}:
            raise ValueError("Invalid assignment status.")

        if not title.strip() or not description.strip():
            raise ValueError("Title and description are required.")

        # Validate the deadline format.
        try:
            datetime.fromisoformat(deadline)
        except (ValueError, TypeError):
            raise ValueError(
                "Deadline must be a valid ISO date/time, "
                "for example 2026-12-01T23:59:00."
            )

        connection = get_connection()

        try:
            course = connection.execute(
                """
                SELECT id
                FROM courses
                WHERE id = ? AND professor_id = ?
                """,
                (course_id, created_by)
            ).fetchone()

            if not course:
                raise ValueError(
                    "Course not found or you do not own this course."
                )

            cursor = connection.execute(
                """
                INSERT INTO assignments (
                    course_id,
                    title,
                    description,
                    instructions,
                    maximum_marks,
                    deadline,
                    created_by,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    course_id,
                    title.strip(),
                    description.strip(),
                    instructions,
                    maximum_marks,
                    deadline,
                    created_by,
                    status
                )
            )

            connection.commit()

            return {
                "id": cursor.lastrowid,
                "course_id": course_id,
                "title": title.strip(),
                "description": description.strip(),
                "instructions": instructions,
                "maximum_marks": maximum_marks,
                "deadline": deadline,
                "status": status
            }

        except sqlite3.IntegrityError:
            connection.rollback()
            raise ValueError("Could not create the assignment.")

        finally:
            connection.close()

    @staticmethod
    def list_course_assignments(course_id, user):
        connection = get_connection()

        try:
            role = user["role"]
            user_id = user["id"]

            if role == "professor":
                course = connection.execute(
                    """
                    SELECT id
                    FROM courses
                    WHERE id = ? AND professor_id = ?
                    """,
                    (course_id, user_id)
                ).fetchone()

                if not course:
                    raise ValueError(
                        "You do not have access to this course."
                    )

                query = """
                    SELECT *
                    FROM assignments
                    WHERE course_id = ?
                    ORDER BY created_at DESC
                """

                rows = connection.execute(
                    query, (course_id,)
                ).fetchall()

            elif role == "student":
                enrollment = connection.execute(
                    """
                    SELECT id
                    FROM enrollments
                    WHERE course_id = ? AND student_id = ?
                    """,
                    (course_id, user_id)
                ).fetchone()

                if not enrollment:
                    raise ValueError(
                        "You are not enrolled in this course."
                    )

                rows = connection.execute(
                    """
                    SELECT *
                    FROM assignments
                    WHERE course_id = ?
                    AND status = 'published'
                    ORDER BY deadline ASC
                    """,
                    (course_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            connection.close()