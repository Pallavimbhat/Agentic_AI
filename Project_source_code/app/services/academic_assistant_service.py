
from app.database.connection import get_connection


class AcademicAssistantService:

    @staticmethod
    def get_accessible_courses(user_id, role):
        """Retrieve courses accessible to the logged-in user."""

        conn = get_connection()

        try:
            if role == "professor":
                rows = conn.execute(
                    """
                    SELECT id, course_code, course_name, description, semester
                    FROM courses
                    WHERE professor_id = ?
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "student":
                rows = conn.execute(
                    """
                    SELECT c.id, c.course_code, c.course_name,
                           c.description, c.semester
                    FROM courses c
                    JOIN enrollments e ON c.id = e.course_id
                    WHERE e.student_id = ?
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @staticmethod
    def get_assignments(user_id, role):
        """Retrieve assignments belonging to accessible courses."""

        conn = get_connection()

        try:
            if role == "professor":
                rows = conn.execute(
                    """
                    SELECT a.*, c.course_name, c.course_code
                    FROM assignments a
                    JOIN courses c ON a.course_id = c.id
                    WHERE c.professor_id = ?
                    ORDER BY a.deadline
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "student":
                rows = conn.execute(
                    """
                    SELECT a.*, c.course_name, c.course_code
                    FROM assignments a
                    JOIN courses c ON a.course_id = c.id
                    JOIN enrollments e ON c.id = e.course_id
                    WHERE e.student_id = ?
                    ORDER BY a.deadline
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @staticmethod
    def get_notes(user_id, role):
        """Retrieve notes from accessible courses."""

        conn = get_connection()

        try:
            if role == "professor":
                rows = conn.execute(
                    """
                    SELECT n.id, n.course_id, n.title, n.description,
                           n.current_version, n.created_at,
                           c.course_name, c.course_code
                    FROM notes n
                    JOIN courses c ON n.course_id = c.id
                    WHERE c.professor_id = ? AND n.is_active = 1
                    ORDER BY n.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "student":
                rows = conn.execute(
                    """
                    SELECT n.id, n.course_id, n.title, n.description,
                           n.current_version, n.created_at,
                           c.course_name, c.course_code
                    FROM notes n
                    JOIN courses c ON n.course_id = c.id
                    JOIN enrollments e ON c.id = e.course_id
                    WHERE e.student_id = ? AND n.is_active = 1
                    ORDER BY n.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @staticmethod
    def get_projects(user_id, role):
        """Retrieve projects accessible to the user."""

        conn = get_connection()

        try:
            if role == "professor":
                rows = conn.execute(
                    """
                    SELECT p.*, c.course_name, c.course_code
                    FROM projects p
                    JOIN courses c ON p.course_id = c.id
                    WHERE c.professor_id = ?
                    ORDER BY p.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "student":
                rows = conn.execute(
                    """
                    SELECT p.*, c.course_name, c.course_code
                    FROM projects p
                    JOIN courses c ON p.course_id = c.id
                    WHERE p.student_id = ?
                    ORDER BY p.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @staticmethod
    def get_grades(user_id, role):
        """Retrieve grades according to the user's role."""

        conn = get_connection()

        try:
            if role == "student":
                rows = conn.execute(
                    """
                    SELECT g.*, a.title AS assignment_title,
                           a.course_id, c.course_name
                    FROM grades g
                    JOIN submissions s ON g.submission_id = s.id
                    JOIN assignments a ON s.assignment_id = a.id
                    JOIN courses c ON a.course_id = c.id
                    WHERE s.student_id = ?
                      AND g.status = 'published'
                    ORDER BY g.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "professor":
                rows = conn.execute(
                    """
                    SELECT g.*, a.title AS assignment_title,
                           a.course_id, c.course_name,
                           s.student_id, s.id AS submission_id
                    FROM grades g
                    JOIN submissions s ON g.submission_id = s.id
                    JOIN assignments a ON s.assignment_id = a.id
                    JOIN courses c ON a.course_id = c.id
                    WHERE c.professor_id = ?
                    ORDER BY g.created_at DESC
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @staticmethod
    def get_milestones(user_id, role):
        """Retrieve project milestones accessible to the user."""

        conn = get_connection()

        try:
            if role == "student":
                rows = conn.execute(
                    """
                    SELECT m.*, p.title AS project_title,
                           p.student_id
                    FROM project_milestones m
                    JOIN projects p ON m.project_id = p.id
                    WHERE p.student_id = ?
                    ORDER BY m.deadline
                    """,
                    (user_id,)
                ).fetchall()

            elif role == "professor":
                rows = conn.execute(
                    """
                    SELECT m.*, p.title AS project_title,
                           p.student_id
                    FROM project_milestones m
                    JOIN projects p ON m.project_id = p.id
                    JOIN courses c ON p.course_id = c.id
                    WHERE c.professor_id = ?
                    ORDER BY m.deadline
                    """,
                    (user_id,)
                ).fetchall()

            else:
                raise ValueError("Invalid user role.")

            return [dict(row) for row in rows]

        finally:
            conn.close()

    @classmethod
    def get_academic_context(cls, user_id, role):
        """
        Collect academic information available to the logged-in user.
        This will later serve as context for the AI assistant.
        """

        return {
            "courses": cls.get_accessible_courses(user_id, role),
            "assignments": cls.get_assignments(user_id, role),
            "notes": cls.get_notes(user_id, role),
            "grades": cls.get_grades(user_id, role),
            "projects": cls.get_projects(user_id, role),
            "milestones": cls.get_milestones(user_id, role)
        }
