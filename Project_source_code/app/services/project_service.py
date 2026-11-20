
from datetime import datetime
from app.database.connection import get_connection


class ProjectService:

    @staticmethod
    def create_project(
        professor_id,
        course_id,
        student_id,
        title,
        description=None
    ):
        if not title or not title.strip():
            raise ValueError("Project title is required.")

        connection = get_connection()

        try:
            course = connection.execute(
                """
                SELECT id FROM courses
                WHERE id = ? AND professor_id = ?
                """,
                (course_id, professor_id)
            ).fetchone()

            if not course:
                raise ValueError(
                    "Course not found or not managed by this professor."
                )

            student = connection.execute(
                """
                SELECT id FROM users
                WHERE id = ? AND role = 'student' AND is_active = 1
                """,
                (student_id,)
            ).fetchone()

            if not student:
                raise ValueError("Active student not found.")

            enrollment = connection.execute(
                """
                SELECT id FROM enrollments
                WHERE course_id = ? AND student_id = ?
                """,
                (course_id, student_id)
            ).fetchone()

            if not enrollment:
                raise ValueError(
                    "Student is not enrolled in this course."
                )

            cursor = connection.execute(
                """
                INSERT INTO projects (
                    course_id,
                    student_id,
                    title,
                    description,
                    status
                )
                VALUES (?, ?, ?, ?, 'ongoing')
                """,
                (
                    course_id,
                    student_id,
                    title.strip(),
                    description
                )
            )

            connection.commit()

            return {
                "success": True,
                "message": "Project created successfully.",
                "project_id": cursor.lastrowid
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def get_student_projects(student_id):
        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT
                    p.id,
                    p.title,
                    p.description,
                    p.status,
                    p.created_at,
                    c.course_code,
                    c.course_name
                FROM projects p
                JOIN courses c ON c.id = p.course_id
                WHERE p.student_id = ?
                ORDER BY p.created_at DESC
                """,
                (student_id,)
            ).fetchall()

            return {
                "success": True,
                "projects": [dict(row) for row in rows]
            }

        finally:
            connection.close()

    @staticmethod
    def get_professor_projects(professor_id):
        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT
                    p.id,
                    p.title,
                    p.description,
                    p.status,
                    p.created_at,
                    u.full_name AS student_name,
                    c.course_code,
                    c.course_name
                FROM projects p
                JOIN courses c ON c.id = p.course_id
                JOIN users u ON u.id = p.student_id
                WHERE c.professor_id = ?
                ORDER BY p.created_at DESC
                """,
                (professor_id,)
            ).fetchall()

            return {
                "success": True,
                "projects": [dict(row) for row in rows]
            }

        finally:
            connection.close()

    @staticmethod
    def create_milestone(
        professor_id,
        project_id,
        title,
        description=None,
        deadline=None
    ):
        if not title or not title.strip():
            raise ValueError("Milestone title is required.")

        connection = get_connection()

        try:
            project = connection.execute(
                """
                SELECT p.id
                FROM projects p
                JOIN courses c ON c.id = p.course_id
                WHERE p.id = ? AND c.professor_id = ?
                """,
                (project_id, professor_id)
            ).fetchone()

            if not project:
                raise ValueError(
                    "Project not found or not managed by this professor."
                )

            cursor = connection.execute(
                """
                INSERT INTO project_milestones (
                    project_id,
                    title,
                    description,
                    deadline,
                    status
                )
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (
                    project_id,
                    title.strip(),
                    description,
                    deadline
                )
            )

            connection.commit()

            return {
                "success": True,
                "message": "Milestone created successfully.",
                "milestone_id": cursor.lastrowid
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def get_project_milestones(project_id, user_id, role):
        connection = get_connection()

        try:
            if role == "professor":
                project = connection.execute(
                    """
                    SELECT p.id
                    FROM projects p
                    JOIN courses c ON c.id = p.course_id
                    WHERE p.id = ? AND c.professor_id = ?
                    """,
                    (project_id, user_id)
                ).fetchone()

            elif role == "student":
                project = connection.execute(
                    """
                    SELECT id FROM projects
                    WHERE id = ? AND student_id = ?
                    """,
                    (project_id, user_id)
                ).fetchone()

            else:
                project = None

            if not project:
                raise ValueError("Project not found or access denied.")

            rows = connection.execute(
                """
                SELECT
                    id,
                    project_id,
                    title,
                    description,
                    deadline,
                    status,
                    completed_at
                FROM project_milestones
                WHERE project_id = ?
                ORDER BY deadline ASC, id ASC
                """,
                (project_id,)
            ).fetchall()

            return {
                "success": True,
                "milestones": [dict(row) for row in rows]
            }

        finally:
            connection.close()

    @staticmethod
    def update_milestone(
        student_id,
        milestone_id,
        status
    ):
        allowed_statuses = {
            "pending",
            "in_progress",
            "completed"
        }

        if status not in allowed_statuses:
            raise ValueError("Invalid milestone status.")

        connection = get_connection()

        try:
            milestone = connection.execute(
                """
                SELECT m.id
                FROM project_milestones m
                JOIN projects p ON p.id = m.project_id
                WHERE m.id = ? AND p.student_id = ?
                """,
                (milestone_id, student_id)
            ).fetchone()

            if not milestone:
                raise ValueError(
                    "Milestone not found or access denied."
                )

            completed_at = (
                datetime.now().isoformat(timespec="seconds")
                if status == "completed"
                else None
            )

            connection.execute(
                """
                UPDATE project_milestones
                SET status = ?, completed_at = ?
                WHERE id = ?
                """,
                (status, completed_at, milestone_id)
            )

            connection.commit()

            return {
                "success": True,
                "message": "Milestone progress updated successfully."
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
