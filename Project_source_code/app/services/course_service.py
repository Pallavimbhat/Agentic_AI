import sqlite3

from app.database.connection import get_connection


class CourseService:

    @staticmethod
    def create_course(course_code, course_name, description, semester, professor_id):

        connection = get_connection()

        try:
            cursor = connection.execute(
                """
                INSERT INTO courses
                (course_code, course_name, description, semester, professor_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    course_code.strip().upper(),
                    course_name.strip(),
                    description,
                    semester,
                    professor_id
                )
            )

            connection.commit()

            return {
                "id": cursor.lastrowid,
                "course_code": course_code.strip().upper(),
                "course_name": course_name.strip(),
                "description": description,
                "semester": semester,
                "professor_id": professor_id
            }

        except sqlite3.IntegrityError:
            connection.rollback()
            raise ValueError("Course code already exists or course data is invalid.")

        finally:
            connection.close()

    @staticmethod
    def list_courses():

        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT c.*, u.full_name AS professor_name
                FROM courses c
                LEFT JOIN users u ON c.professor_id = u.id
                ORDER BY c.id DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()

    @staticmethod
    def list_professor_courses(professor_id):

        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM courses
                WHERE professor_id = ?
                ORDER BY id DESC
                """,
                (professor_id,)
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()

    @staticmethod
    def enroll_student(course_id, student_id):

        connection = get_connection()

        try:
            course = connection.execute(
                "SELECT id FROM courses WHERE id = ?",
                (course_id,)
            ).fetchone()

            if course is None:
                raise ValueError("Course not found.")

            student = connection.execute(
                """
                SELECT id FROM users
                WHERE id = ? AND role = 'student' AND is_active = 1
                """,
                (student_id,)
            ).fetchone()

            if student is None:
                raise ValueError("Valid student account not found.")

            connection.execute(
                """
                INSERT INTO enrollments (student_id, course_id)
                VALUES (?, ?)
                """,
                (student_id, course_id)
            )

            connection.commit()

            return {
                "student_id": student_id,
                "course_id": course_id,
                "message": "Student enrolled successfully."
            }

        except sqlite3.IntegrityError:
            connection.rollback()
            raise ValueError("Student is already enrolled in this course.")

        finally:
            connection.close()

    @staticmethod
    def list_student_courses(student_id):

        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT c.*
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id
                WHERE e.student_id = ?
                ORDER BY c.id DESC
                """,
                (student_id,)
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()