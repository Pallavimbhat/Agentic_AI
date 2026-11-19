"""Database service layer for the Course Organizer.

All SQL values are parameterized. Connections are closed after every operation.
This service provides database operations used by the course organizer agents.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(__file__).resolve().parent / "course_organizer.db"


class DatabaseService:
    """Provides validated, reusable database operations."""

    def __init__(self, database_path: Path | str = DATABASE_PATH):
        self.database_path = str(database_path)
        if not Path(self.database_path).exists():
            raise FileNotFoundError(
                f"Database file not found: {self.database_path}. "
                "Initialize the database first."
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _execute(self, query: str, values: tuple = ()):
        with self._connect() as connection:
            cursor = connection.execute(query, values)
            return cursor.lastrowid

    def _fetch_all(self, query: str, values: tuple = ()):
        with self._connect() as connection:
            rows = connection.execute(query, values).fetchall()
            return [dict(row) for row in rows]

    def _fetch_one(self, query: str, values: tuple = ()):
        with self._connect() as connection:
            row = connection.execute(query, values).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _required_text(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must not be empty.")
        return value.strip()

    @staticmethod
    def _validate_deadline(deadline: str) -> str:
        deadline = DatabaseService._required_text(deadline, "Deadline")
        try:
            datetime.fromisoformat(deadline)
        except ValueError as error:
            raise ValueError(
                "Deadline must use ISO format, such as 2026-11-15 "
                "or 2026-11-15T23:59:00."
            ) from error
        return deadline

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    def create_user(self, name: str, email: str, role: str):
        name = self._required_text(name, "Name")
        email = self._required_text(email, "Email").lower()
        role = self._required_text(role, "Role").lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        if role not in {"admin", "professor", "student"}:
            raise ValueError("Role must be admin, professor, or student.")
        user_id = self._execute(
            "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
            (name, email, role),
        )
        return self.get_user(user_id)

    def get_user(self, user_id: int):
        return self._fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def list_users(self, role: str | None = None):
        if role is not None:
            if role not in {"admin", "professor", "student"}:
                raise ValueError("Invalid role.")
            return self._fetch_all(
                "SELECT * FROM users WHERE role = ? ORDER BY id", (role,)
            )
        return self._fetch_all("SELECT * FROM users ORDER BY id")

    # ------------------------------------------------------------------
    # Courses and enrollments
    # ------------------------------------------------------------------
    def create_course(
        self,
        course_code: str,
        name: str,
        semester: int,
        description: str = "",
        created_by: int | None = None,
    ):
        course_code = self._required_text(course_code, "Course code").upper()
        name = self._required_text(name, "Course name")
        if isinstance(semester, bool) or not isinstance(semester, int):
            raise ValueError("Semester must be an integer.")
        if not 1 <= semester <= 12:
            raise ValueError("Semester must be between 1 and 12.")
        if created_by is not None:
            user = self.get_user(created_by)
            if not user:
                raise ValueError("The specified creator does not exist.")
            if user["role"] not in {"admin", "professor"}:
                raise ValueError("Only an admin or professor can create courses.")
        course_id = self._execute(
            """INSERT INTO courses
               (course_code, name, semester, description, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (course_code, name, semester, description.strip(), created_by),
        )
        return self.get_course(course_id)

    def get_course(self, course_id: int):
        return self._fetch_one("SELECT * FROM courses WHERE id = ?", (course_id,))

    def list_courses(self, search: str = ""):
        search = search.strip()
        if search:
            return self._fetch_all(
                """SELECT * FROM courses
                   WHERE course_code LIKE ? OR name LIKE ?
                   ORDER BY id""",
                (f"%{search}%", f"%{search}%"),
            )
        return self._fetch_all("SELECT * FROM courses ORDER BY id")

    def update_course(
        self,
        course_id: int,
        name: str | None = None,
        semester: int | None = None,
        description: str | None = None,
    ):
        course = self.get_course(course_id)
        if not course:
            raise ValueError("Course not found.")
        new_name = course["name"] if name is None else self._required_text(name, "Course name")
        new_semester = course["semester"] if semester is None else semester
        if (
            isinstance(new_semester, bool)
            or not isinstance(new_semester, int)
            or not 1 <= new_semester <= 12
        ):
            raise ValueError("Semester must be an integer between 1 and 12.")
        new_description = (
            course["description"] if description is None else description.strip()
        )
        self._execute(
            """UPDATE courses
               SET name = ?, semester = ?, description = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_name, new_semester, new_description, course_id),
        )
        return self.get_course(course_id)

    def delete_course(self, course_id: int):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        self._execute("DELETE FROM courses WHERE id = ?", (course_id,))
        return {"deleted": True, "course_id": course_id}

    def enroll_student(self, course_id: int, student_id: int):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        student = self.get_user(student_id)
        if not student or student["role"] != "student":
            raise ValueError("A valid student user is required.")
        self._execute(
            """INSERT INTO course_enrollments (course_id, student_id)
               VALUES (?, ?)""",
            (course_id, student_id),
        )
        return self._fetch_one(
            """SELECT * FROM course_enrollments
               WHERE course_id = ? AND student_id = ?""",
            (course_id, student_id),
        )

    def list_course_students(self, course_id: int):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        return self._fetch_all(
            """SELECT u.id, u.name, u.email, u.role, e.enrolled_at
               FROM course_enrollments e
               JOIN users u ON u.id = e.student_id
               WHERE e.course_id = ? ORDER BY u.name""",
            (course_id,),
        )

    # ------------------------------------------------------------------
    # Notes and note version history
    # ------------------------------------------------------------------
    def create_note(
        self, course_id: int, title: str, content: str,
        created_by: int | None = None, file_path: str | None = None,
    ):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        title = self._required_text(title, "Note title")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Note content must not be empty.")
        if created_by is not None and not self.get_user(created_by):
            raise ValueError("Creator not found.")
        note_id = self._execute(
            """INSERT INTO notes (course_id, title, created_by)
               VALUES (?, ?, ?)""",
            (course_id, title, created_by),
        )
        self._execute(
            """INSERT INTO note_versions
               (note_id, version_number, content, file_path, created_by)
               VALUES (?, 1, ?, ?, ?)""",
            (note_id, content, file_path, created_by),
        )
        return self.get_note(note_id)

    def get_note(self, note_id: int):
        note = self._fetch_one("SELECT * FROM notes WHERE id = ?", (note_id,))
        if not note:
            return None
        note["latest_version"] = self._fetch_one(
            """SELECT id, note_id, version_number, content, file_path,
                      created_by, created_at
               FROM note_versions
               WHERE note_id = ? AND version_number = ?""",
            (note_id, note["current_version"]),
        )
        return note

    def list_notes(self, course_id: int | None = None, search: str = ""):
        clauses, values = [], []
        if course_id is not None:
            clauses.append("course_id = ?")
            values.append(course_id)
        if search.strip():
            clauses.append("title LIKE ?")
            values.append(f"%{search.strip()}%")
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return self._fetch_all(
            f"SELECT * FROM notes{where} ORDER BY updated_at DESC, id DESC",
            tuple(values),
        )

    def add_note_version(
        self, note_id: int, content: str, created_by: int | None = None,
        file_path: str | None = None, title: str | None = None,
    ):
        note = self.get_note(note_id)
        if not note:
            raise ValueError("Note not found.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Note content must not be empty.")
        if created_by is not None and not self.get_user(created_by):
            raise ValueError("Creator not found.")
        next_version = note["current_version"] + 1
        self._execute(
            """INSERT INTO note_versions
               (note_id, version_number, content, file_path, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (note_id, next_version, content, file_path, created_by),
        )
        if title is not None:
            title = self._required_text(title, "Note title")
            self._execute(
                """UPDATE notes SET title = ?, current_version = ?,
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (title, next_version, note_id),
            )
        else:
            self._execute(
                """UPDATE notes SET current_version = ?,
                   updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (next_version, note_id),
            )
        return self.get_note(note_id)

    def get_note_versions(self, note_id: int):
        if not self.get_note(note_id):
            raise ValueError("Note not found.")
        return self._fetch_all(
            """SELECT * FROM note_versions
               WHERE note_id = ? ORDER BY version_number DESC""",
            (note_id,),
        )

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------
    def create_assignment(
        self, course_id: int, title: str, deadline: str,
        description: str = "", max_marks: float = 100,
        created_by: int | None = None,
    ):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        title = self._required_text(title, "Assignment title")
        deadline = self._validate_deadline(deadline)
        if isinstance(max_marks, bool) or not isinstance(max_marks, (int, float)):
            raise ValueError("Maximum marks must be a number.")
        if max_marks <= 0:
            raise ValueError("Maximum marks must be greater than zero.")
        if created_by is not None:
            user = self.get_user(created_by)
            if not user or user["role"] not in {"admin", "professor"}:
                raise ValueError("A valid admin or professor is required.")
        assignment_id = self._execute(
            """INSERT INTO assignments
               (course_id, title, description, deadline, max_marks, created_by)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (course_id, title, description.strip(), deadline, max_marks, created_by),
        )
        return self.get_assignment(assignment_id)

    def get_assignment(self, assignment_id: int):
        return self._fetch_one("SELECT * FROM assignments WHERE id = ?", (assignment_id,))

    def list_assignments(self, course_id: int | None = None):
        if course_id is not None:
            return self._fetch_all(
                "SELECT * FROM assignments WHERE course_id = ? ORDER BY deadline",
                (course_id,),
            )
        return self._fetch_all("SELECT * FROM assignments ORDER BY deadline")

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------
    def submit_assignment(
        self, assignment_id: int, student_id: int,
        content: str = "", file_path: str | None = None,
        submitted_at: str | None = None,
    ):
        assignment = self.get_assignment(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found.")
        student = self.get_user(student_id)
        if not student or student["role"] != "student":
            raise ValueError("A valid student user is required.")
        if not content.strip() and not file_path:
            raise ValueError("Provide submission content or a file path.")
        timestamp = submitted_at or datetime.now().isoformat(timespec="seconds")
        try:
            submitted_dt = datetime.fromisoformat(timestamp)
            deadline_dt = datetime.fromisoformat(assignment["deadline"])
        except ValueError as error:
            raise ValueError("Submission and assignment dates must use ISO format.") from error
        status = "late" if submitted_dt > deadline_dt else "submitted"
        existing = self._fetch_one(
            """SELECT id FROM submissions
               WHERE assignment_id = ? AND student_id = ?""",
            (assignment_id, student_id),
        )
        if existing:
            self._execute(
                """UPDATE submissions SET content = ?, file_path = ?, status = ?,
                   submitted_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
                (content, file_path, status, timestamp, existing["id"]),
            )
            submission_id = existing["id"]
        else:
            submission_id = self._execute(
                """INSERT INTO submissions
                   (assignment_id, student_id, content, file_path, status, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (assignment_id, student_id, content, file_path, status, timestamp),
            )
        return self.get_submission(submission_id)

    def get_submission(self, submission_id: int):
        return self._fetch_one(
            """SELECT s.*, a.title AS assignment_title, a.max_marks,
                      u.name AS student_name
               FROM submissions s
               JOIN assignments a ON a.id = s.assignment_id
               JOIN users u ON u.id = s.student_id
               WHERE s.id = ?""",
            (submission_id,),
        )

    def list_submissions(
        self, assignment_id: int | None = None, student_id: int | None = None,
        status: str | None = None,
    ):
        clauses, values = [], []
        if assignment_id is not None:
            clauses.append("s.assignment_id = ?")
            values.append(assignment_id)
        if student_id is not None:
            clauses.append("s.student_id = ?")
            values.append(student_id)
        if status is not None:
            if status not in {"draft", "submitted", "late", "reviewed"}:
                raise ValueError("Invalid submission status.")
            clauses.append("s.status = ?")
            values.append(status)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return self._fetch_all(
            """SELECT s.*, a.title AS assignment_title, u.name AS student_name
               FROM submissions s
               JOIN assignments a ON a.id = s.assignment_id
               JOIN users u ON u.id = s.student_id"""
            + where + " ORDER BY s.submitted_at DESC",
            tuple(values),
        )

    def update_submission_status(self, submission_id: int, status: str):
        if status not in {"draft", "submitted", "late", "reviewed"}:
            raise ValueError("Invalid submission status.")
        if not self.get_submission(submission_id):
            raise ValueError("Submission not found.")
        self._execute(
            """UPDATE submissions SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, submission_id),
        )
        return self.get_submission(submission_id)

    # ------------------------------------------------------------------
    # Similarity reports (store results; a human reviews them)
    # ------------------------------------------------------------------
    def create_similarity_report(
        self, submission_id: int, similarity_score: float,
        compared_submission_id: int | None = None, details: str = "",
    ):
        if not self.get_submission(submission_id):
            raise ValueError("Submission not found.")
        if compared_submission_id is not None and not self.get_submission(compared_submission_id):
            raise ValueError("Compared submission not found.")
        if isinstance(similarity_score, bool) or not isinstance(similarity_score, (int, float)):
            raise ValueError("Similarity score must be numeric.")
        if not 0 <= similarity_score <= 100:
            raise ValueError("Similarity score must be between 0 and 100.")
        report_id = self._execute(
            """INSERT INTO similarity_reports
               (submission_id, compared_submission_id, similarity_score, details)
               VALUES (?, ?, ?, ?)""",
            (submission_id, compared_submission_id, float(similarity_score), details),
        )
        return self.get_similarity_report(report_id)

    def get_similarity_report(self, report_id: int):
        return self._fetch_one(
            """SELECT r.*, s.student_id, s.assignment_id
               FROM similarity_reports r
               JOIN submissions s ON s.id = r.submission_id
               WHERE r.id = ?""",
            (report_id,),
        )

    def list_similarity_reports(
        self, submission_id: int | None = None, min_score: float | None = None,
    ):
        clauses, values = [], []
        if submission_id is not None:
            clauses.append("submission_id = ?")
            values.append(submission_id)
        if min_score is not None:
            if not 0 <= min_score <= 100:
                raise ValueError("Minimum score must be between 0 and 100.")
            clauses.append("similarity_score >= ?")
            values.append(min_score)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return self._fetch_all(
            "SELECT * FROM similarity_reports" + where + " ORDER BY similarity_score DESC",
            tuple(values),
        )

    def review_similarity_report(self, report_id: int, reviewed_by: int):
        report = self.get_similarity_report(report_id)
        if not report:
            raise ValueError("Similarity report not found.")
        reviewer = self.get_user(reviewed_by)
        if not reviewer or reviewer["role"] not in {"admin", "professor"}:
            raise ValueError("A valid admin or professor reviewer is required.")
        self._execute(
            "UPDATE similarity_reports SET reviewed_by = ? WHERE id = ?",
            (reviewed_by, report_id),
        )
        return self.get_similarity_report(report_id)

    # ------------------------------------------------------------------
    # Grades: draft -> approved -> published
    # ------------------------------------------------------------------
    def create_or_update_grade(
        self, submission_id: int, marks: float | None,
        feedback: str = "", graded_by: int | None = None,
    ):
        submission = self.get_submission(submission_id)
        if not submission:
            raise ValueError("Submission not found.")
        if marks is not None:
            if isinstance(marks, bool) or not isinstance(marks, (int, float)):
                raise ValueError("Marks must be numeric.")
            if marks < 0 or marks > submission["max_marks"]:
                raise ValueError(
                    f"Marks must be between 0 and {submission['max_marks']}."
                )
        if graded_by is not None:
            grader = self.get_user(graded_by)
            if not grader or grader["role"] not in {"admin", "professor"}:
                raise ValueError("A valid admin or professor grader is required.")
        existing = self._fetch_one(
            "SELECT * FROM grades WHERE submission_id = ?", (submission_id,)
        )
        if existing and existing["status"] != "draft":
            raise ValueError("Only draft grades can be edited.")
        if existing:
            self._execute(
                """UPDATE grades SET marks = ?, feedback = ?, graded_by = ?,
                   updated_at = CURRENT_TIMESTAMP WHERE submission_id = ?""",
                (marks, feedback, graded_by, submission_id),
            )
            grade_id = existing["id"]
        else:
            grade_id = self._execute(
                """INSERT INTO grades (submission_id, marks, feedback, graded_by)
                   VALUES (?, ?, ?, ?)""",
                (submission_id, marks, feedback, graded_by),
            )
        return self.get_grade(grade_id)

    def get_grade(self, grade_id: int):
        return self._fetch_one(
            """SELECT g.*, s.student_id, s.assignment_id, a.max_marks,
                      u.name AS student_name
               FROM grades g
               JOIN submissions s ON s.id = g.submission_id
               JOIN assignments a ON a.id = s.assignment_id
               JOIN users u ON u.id = s.student_id
               WHERE g.id = ?""",
            (grade_id,),
        )

    def list_grades(self, status: str | None = None, student_id: int | None = None):
        clauses, values = [], []
        if status is not None:
            if status not in {"draft", "approved", "published"}:
                raise ValueError("Invalid grade status.")
            clauses.append("g.status = ?")
            values.append(status)
        if student_id is not None:
            clauses.append("s.student_id = ?")
            values.append(student_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        return self._fetch_all(
            """SELECT g.*, s.student_id, s.assignment_id, a.max_marks,
                      u.name AS student_name
               FROM grades g JOIN submissions s ON s.id = g.submission_id
               JOIN assignments a ON a.id = s.assignment_id
               JOIN users u ON u.id = s.student_id"""
            + where + " ORDER BY g.updated_at DESC",
            tuple(values),
        )

    def approve_grade(self, grade_id: int, approved_by: int):
        grade = self.get_grade(grade_id)
        if not grade:
            raise ValueError("Grade not found.")
        if grade["status"] != "draft":
            raise ValueError("Only draft grades can be approved.")
        if grade["marks"] is None:
            raise ValueError("A grade must have marks before approval.")
        approver = self.get_user(approved_by)
        if not approver or approver["role"] not in {"admin", "professor"}:
            raise ValueError("A valid admin or professor approver is required.")
        self._execute(
            """UPDATE grades SET status = 'approved', approved_by = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (approved_by, grade_id),
        )
        return self.get_grade(grade_id)

    def publish_grade(self, grade_id: int):
        grade = self.get_grade(grade_id)
        if not grade:
            raise ValueError("Grade not found.")
        if grade["status"] != "approved":
            raise ValueError("Only approved grades can be published.")
        self._execute(
            """UPDATE grades SET status = 'published', published_at = CURRENT_TIMESTAMP,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (grade_id,),
        )
        return self.get_grade(grade_id)

    # ------------------------------------------------------------------
    # Project milestones
    # ------------------------------------------------------------------
    def create_milestone(
        self, course_id: int, title: str, deadline: str,
        description: str = "", created_by: int | None = None,
    ):
        if not self.get_course(course_id):
            raise ValueError("Course not found.")
        title = self._required_text(title, "Milestone title")
        deadline = self._validate_deadline(deadline)
        if created_by is not None:
            user = self.get_user(created_by)
            if not user or user["role"] not in {"admin", "professor"}:
                raise ValueError("A valid admin or professor is required.")
        milestone_id = self._execute(
            """INSERT INTO project_milestones
               (course_id, title, deadline, description, created_by)
               VALUES (?, ?, ?, ?, ?)""",
            (course_id, title, deadline, description.strip(), created_by),
        )
        return self.get_milestone(milestone_id)

    def get_milestone(self, milestone_id: int):
        return self._fetch_one(
            "SELECT * FROM project_milestones WHERE id = ?", (milestone_id,)
        )

    def list_milestones(self, course_id: int | None = None):
        if course_id is not None:
            return self._fetch_all(
                """SELECT * FROM project_milestones
                   WHERE course_id = ? ORDER BY deadline""",
                (course_id,),
            )
        return self._fetch_all("SELECT * FROM project_milestones ORDER BY deadline")

    def update_milestone(self, milestone_id: int, status: str, progress: int):
        if not self.get_milestone(milestone_id):
            raise ValueError("Milestone not found.")
        if status not in {"pending", "in_progress", "completed", "overdue"}:
            raise ValueError("Invalid milestone status.")
        if isinstance(progress, bool) or not isinstance(progress, int):
            raise ValueError("Progress must be an integer.")
        if not 0 <= progress <= 100:
            raise ValueError("Progress must be between 0 and 100.")
        if status == "completed" and progress != 100:
            raise ValueError("A completed milestone must have 100% progress.")
        self._execute(
            """UPDATE project_milestones SET status = ?, progress = ?,
               updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
            (status, progress, milestone_id),
        )
        return self.get_milestone(milestone_id)

    # ------------------------------------------------------------------
    # Audit logs
    # ------------------------------------------------------------------
    def log_action(
        self, actor_type: str, action: str, entity_type: str,
        outcome: str, actor_id: int | None = None, agent_name: str | None = None,
        entity_id: int | None = None, details: str | dict[str, Any] = "",
    ):
        actor_type = self._required_text(actor_type, "Actor type")
        action = self._required_text(action, "Action")
        entity_type = self._required_text(entity_type, "Entity type")
        if outcome not in {"success", "failure"}:
            raise ValueError("Outcome must be success or failure.")
        if actor_id is not None and not self.get_user(actor_id):
            raise ValueError("Actor user not found.")
        if isinstance(details, dict):
            details = json.dumps(details, ensure_ascii=False)
        elif not isinstance(details, str):
            raise ValueError("Details must be a string or dictionary.")
        log_id = self._execute(
            """INSERT INTO audit_logs
               (actor_type, actor_id, agent_name, action, entity_type,
                entity_id, outcome, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (actor_type, actor_id, agent_name, action, entity_type,
             entity_id, outcome, details),
        )
        return self._fetch_one("SELECT * FROM audit_logs WHERE id = ?", (log_id,))

    def list_audit_logs(
        self, entity_type: str | None = None, entity_id: int | None = None,
        limit: int = 100,
    ):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer.")
        clauses, values = [], []
        if entity_type is not None:
            clauses.append("entity_type = ?")
            values.append(entity_type)
        if entity_id is not None:
            clauses.append("entity_id = ?")
            values.append(entity_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        values.append(limit)
        return self._fetch_all(
            "SELECT * FROM audit_logs" + where
            + " ORDER BY created_at DESC, id DESC LIMIT ?",
            tuple(values),
        )

    # ------------------------------------------------------------------
    # Student-scoped academic views
    # ------------------------------------------------------------------
    def list_student_notes(self, student_id: int):
        """List notes only for courses in which this student is enrolled."""
        return self._fetch_all(
            """SELECT n.id, n.course_id, c.course_code, c.name AS course_name,
                      n.title, n.current_version, n.updated_at
               FROM notes n
               JOIN courses c ON c.id = n.course_id
               JOIN course_enrollments e ON e.course_id = n.course_id
               WHERE e.student_id = ?
               ORDER BY c.course_code, n.title""",
            (student_id,),
        )

    def list_student_assignments(self, student_id: int):
        """Return assignments for enrolled courses with this student's submission."""
        rows = self._fetch_all(
            """SELECT a.id AS assignment_id, a.course_id, c.course_code,
                      c.name AS course_name, a.title, a.description,
                      a.deadline, a.max_marks, s.id AS submission_id,
                      s.status AS submission_status, s.submitted_at
               FROM assignments a
               JOIN courses c ON c.id = a.course_id
               JOIN course_enrollments e ON e.course_id = a.course_id
               LEFT JOIN submissions s
                 ON s.assignment_id = a.id AND s.student_id = e.student_id
               WHERE e.student_id = ?
               ORDER BY a.deadline, a.id""",
            (student_id,),
        )
        from datetime import datetime
        now = datetime.now()
        for row in rows:
            try:
                deadline = datetime.fromisoformat(row["deadline"])
                if deadline.tzinfo:
                    deadline = deadline.replace(tzinfo=None)
            except (TypeError, ValueError):
                deadline = None
            submitted = bool(row.get("submission_id"))
            if submitted:
                row["work_status"] = (
                    "Submitted late" if row.get("submission_status") == "late"
                    else "Submitted"
                )
            elif deadline and deadline < now:
                row["work_status"] = "Overdue"
            else:
                row["work_status"] = "Pending"
        return rows

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard_summary(self) -> dict[str, Any]:
        tables = [
            "users", "courses", "course_enrollments", "notes", "note_versions",
            "assignments", "submissions", "similarity_reports", "grades",
            "project_milestones", "audit_logs",
        ]
        summary = {}
        with self._connect() as connection:
            for table in tables:
                summary[table] = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
        return summary
