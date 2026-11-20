from pathlib import Path

from app.database.connection import get_connection


class NotesService:

    # ---------------------------------------------------------
    # COMMON ACCESS CONTROL
    # ---------------------------------------------------------

    @staticmethod
    def _verify_course_access(connection, course_id, user):

        if user["role"] == "professor":

            access = connection.execute(
                """
                SELECT id
                FROM courses
                WHERE id = ? AND professor_id = ?
                """,
                (course_id, user["id"])
            ).fetchone()

        elif user["role"] == "student":

            access = connection.execute(
                """
                SELECT c.id
                FROM courses c
                JOIN enrollments e ON e.course_id = c.id
                WHERE c.id = ?
                AND e.student_id = ?
                AND e.status = 'active'
                """,
                (course_id, user["id"])
            ).fetchone()

        else:
            raise ValueError("Invalid user role.")

        if access is None:
            raise ValueError("You do not have access to this course.")

        return True

    # ---------------------------------------------------------
    # 1. UPLOAD NEW NOTES
    # ---------------------------------------------------------

    @staticmethod
    def upload_note(course_id, title, description, uploaded_by, file_path):

        connection = get_connection()

        try:

            course = connection.execute(
                """
                SELECT id
                FROM courses
                WHERE id = ? AND professor_id = ?
                """,
                (course_id, uploaded_by)
            ).fetchone()

            if course is None:
                raise ValueError(
                    "Course not found or professor does not own this course."
                )

            if not title or not title.strip():
                raise ValueError("Note title is required.")

            if not file_path:
                raise ValueError("A file path is required.")

            cursor = connection.execute(
                """
                INSERT INTO notes (
                    course_id,
                    title,
                    description,
                    uploaded_by,
                    current_version
                )
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    course_id,
                    title.strip(),
                    description,
                    uploaded_by
                )
            )

            note_id = cursor.lastrowid

            connection.execute(
                """
                INSERT INTO note_versions (
                    note_id,
                    version_number,
                    file_path,
                    uploaded_by
                )
                VALUES (?, 1, ?, ?)
                """,
                (note_id, str(file_path), uploaded_by)
            )

            connection.commit()

            return {
                "success": True,
                "note_id": note_id,
                "course_id": course_id,
                "title": title.strip(),
                "version": 1,
                "message": "Notes uploaded successfully."
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 2. GET ALL NOTES FOR A COURSE
    # ---------------------------------------------------------

    @staticmethod
    def get_course_notes(course_id, user):

        connection = get_connection()

        try:

            NotesService._verify_course_access(
                connection,
                course_id,
                user
            )

            rows = connection.execute(
                """
                SELECT
                    n.id AS note_id,
                    n.course_id,
                    n.title,
                    n.description,
                    n.current_version,
                    n.created_at,
                    u.full_name AS uploaded_by_name,
                    nv.uploaded_at
                FROM notes n
                JOIN users u ON n.uploaded_by = u.id
                JOIN note_versions nv
                    ON nv.note_id = n.id
                    AND nv.version_number = n.current_version
                WHERE n.course_id = ?
                AND n.is_active = 1
                ORDER BY n.created_at DESC
                """,
                (course_id,)
            ).fetchall()

            return {
                "success": True,
                "course_id": course_id,
                "notes": [dict(row) for row in rows]
            }

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 3. GET CURRENT NOTE FILE
    # ---------------------------------------------------------

    @staticmethod
    def get_note_file(note_id, user):

        connection = get_connection()

        try:

            note = connection.execute(
                """
                SELECT
                    n.id,
                    n.title,
                    n.course_id,
                    n.current_version,
                    nv.file_path
                FROM notes n
                JOIN note_versions nv
                    ON nv.note_id = n.id
                    AND nv.version_number = n.current_version
                WHERE n.id = ?
                AND n.is_active = 1
                """,
                (note_id,)
            ).fetchone()

            if note is None:
                raise ValueError("Note not found.")

            NotesService._verify_course_access(
                connection,
                note["course_id"],
                user
            )

            return dict(note)

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 4. UPDATE NOTES AND CREATE A NEW VERSION
    # ---------------------------------------------------------

    @staticmethod
    def update_note(
        note_id,
        title,
        description,
        uploaded_by,
        file_path
    ):

        connection = get_connection()

        try:

            note = connection.execute(
                """
                SELECT
                    n.id,
                    n.course_id,
                    n.current_version
                FROM notes n
                JOIN courses c ON c.id = n.course_id
                WHERE n.id = ?
                AND c.professor_id = ?
                AND n.is_active = 1
                """,
                (note_id, uploaded_by)
            ).fetchone()

            if note is None:
                raise ValueError(
                    "Note not found or professor does not own this course."
                )

            if not title or not title.strip():
                raise ValueError("Note title is required.")

            if not file_path:
                raise ValueError("A file path is required.")

            new_version = note["current_version"] + 1

            connection.execute(
                """
                INSERT INTO note_versions (
                    note_id,
                    version_number,
                    file_path,
                    uploaded_by
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    note_id,
                    new_version,
                    str(file_path),
                    uploaded_by
                )
            )

            connection.execute(
                """
                UPDATE notes
                SET title = ?,
                    description = ?,
                    current_version = ?
                WHERE id = ?
                """,
                (
                    title.strip(),
                    description,
                    new_version,
                    note_id
                )
            )

            connection.commit()

            return {
                "success": True,
                "note_id": note_id,
                "version": new_version,
                "message": "Notes updated successfully."
            }

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 5. GET COMPLETE NOTE VERSION HISTORY
    # ---------------------------------------------------------

    @staticmethod
    def get_note_versions(note_id, user):

        connection = get_connection()

        try:

            note = connection.execute(
                """
                SELECT id, course_id, current_version, title
                FROM notes
                WHERE id = ?
                AND is_active = 1
                """,
                (note_id,)
            ).fetchone()

            if note is None:
                raise ValueError("Note not found.")

            NotesService._verify_course_access(
                connection,
                note["course_id"],
                user
            )

            versions = connection.execute(
                """
                SELECT
                    nv.version_number,
                    nv.uploaded_at,
                    u.full_name AS uploaded_by_name
                FROM note_versions nv
                JOIN users u ON u.id = nv.uploaded_by
                WHERE nv.note_id = ?
                ORDER BY nv.version_number DESC
                """,
                (note_id,)
            ).fetchall()

            return {
                "success": True,
                "note_id": note_id,
                "title": note["title"],
                "current_version": note["current_version"],
                "versions": [dict(row) for row in versions]
            }

        finally:
            connection.close()

    # ---------------------------------------------------------
    # 6. DOWNLOAD A SPECIFIC HISTORICAL VERSION
    # ---------------------------------------------------------

    @staticmethod
    def get_note_version_file(note_id, version_number, user):

        connection = get_connection()

        try:

            note = connection.execute(
                """
                SELECT
                    n.id,
                    n.course_id,
                    n.title,
                    nv.version_number,
                    nv.file_path
                FROM notes n
                JOIN note_versions nv ON nv.note_id = n.id
                WHERE n.id = ?
                AND nv.version_number = ?
                AND n.is_active = 1
                """,
                (note_id, version_number)
            ).fetchone()

            if note is None:
                raise ValueError("Note version not found.")

            NotesService._verify_course_access(
                connection,
                note["course_id"],
                user
            )

            return dict(note)

        finally:
            connection.close()