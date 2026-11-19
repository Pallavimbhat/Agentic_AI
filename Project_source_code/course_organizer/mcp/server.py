"""MCP server exposing Course Organizer database operations as MCP tools.

Run from the project root with:
    python -m course_organizer.mcp.server

This uses the official Python MCP SDK (FastMCP) and the existing DatabaseService.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from course_organizer.database.db_service import DatabaseService

mcp = FastMCP("course-organizer")
db = DatabaseService()


@mcp.tool()
def list_courses(search: str = "") -> list[dict]:
    """List courses, optionally searching by course code or course name."""
    return db.list_courses(search=search)


@mcp.tool()
def get_course(course_id: int) -> dict | None:
    """Get a course by its database ID."""
    return db.get_course(course_id)


@mcp.tool()
def create_course(
    course_code: str,
    name: str,
    semester: int,
    description: str = "",
    created_by: int | None = None,
) -> dict:
    """Create a course. created_by, when supplied, must be an admin/professor ID."""
    return db.create_course(
        course_code=course_code,
        name=name,
        semester=semester,
        description=description,
        created_by=created_by,
    )


@mcp.tool()
def list_notes(course_id: int | None = None, search: str = "") -> list[dict]:
    """List course notes, optionally filtering by course ID and title search."""
    return db.list_notes(course_id=course_id, search=search)


@mcp.tool()
def get_note(note_id: int) -> dict | None:
    """Get a note and its current version content."""
    return db.get_note(note_id)


@mcp.tool()
def create_note(
    course_id: int,
    title: str,
    content: str,
    created_by: int | None = None,
    file_path: str | None = None,
) -> dict:
    """Create a note and its first version."""
    return db.create_note(
        course_id=course_id,
        title=title,
        content=content,
        created_by=created_by,
        file_path=file_path,
    )


@mcp.tool()
def add_note_version(
    note_id: int,
    content: str,
    created_by: int | None = None,
    file_path: str | None = None,
    title: str | None = None,
) -> dict:
    """Add a new version to an existing note while preserving version history."""
    return db.add_note_version(
        note_id=note_id,
        content=content,
        created_by=created_by,
        file_path=file_path,
        title=title,
    )


@mcp.tool()
def list_assignments(course_id: int | None = None) -> list[dict]:
    """List assignments, optionally restricted to a course."""
    return db.list_assignments(course_id=course_id)


@mcp.tool()
def list_submissions(
    assignment_id: int | None = None,
    student_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    """List submissions, optionally filtering by assignment, student, or status."""
    return db.list_submissions(
        assignment_id=assignment_id,
        student_id=student_id,
        status=status,
    )


@mcp.tool()
def create_similarity_report(
    submission_id: int,
    similarity_score: float,
    compared_submission_id: int | None = None,
    details: str = "",
) -> dict:
    """Save a similarity score for human review; this tool does not decide misconduct."""
    return db.create_similarity_report(
        submission_id=submission_id,
        similarity_score=similarity_score,
        compared_submission_id=compared_submission_id,
        details=details,
    )


@mcp.tool()
def create_or_update_grade(
    submission_id: int,
    marks: float | None,
    feedback: str = "",
    graded_by: int | None = None,
) -> dict:
    """Create or update a draft grade. Approval and publication are separate steps."""
    return db.create_or_update_grade(
        submission_id=submission_id,
        marks=marks,
        feedback=feedback,
        graded_by=graded_by,
    )


@mcp.tool()
def approve_grade(grade_id: int, approved_by: int) -> dict:
    """Approve a draft grade using an admin or professor account."""
    return db.approve_grade(grade_id=grade_id, approved_by=approved_by)


@mcp.tool()
def publish_grade(grade_id: int) -> dict:
    """Publish a grade only after it has been approved."""
    return db.publish_grade(grade_id=grade_id)


@mcp.tool()
def list_milestones(course_id: int | None = None) -> list[dict]:
    """List project milestones, optionally restricted to a course."""
    return db.list_milestones(course_id=course_id)


@mcp.tool()
def dashboard_summary() -> dict:
    """Return record counts for the course organizer dashboard."""
    return db.dashboard_summary()


if __name__ == "__main__":
    mcp.run()
