from app.tools.tool_registry import ToolRegistry

from app.services.academic_assistant_service import (
    AcademicAssistantService
)

from app.services.assignment_service import AssignmentService
from app.services.submission_service import SubmissionService
from app.services.project_service import ProjectService
from app.services.grading_service import GradingService
from app.services.course_service import CourseService


def list_courses(user_id, role):
    """Retrieve courses associated with the authenticated user."""

    if role == "student":
        return CourseService.list_student_courses(user_id)

    if role == "professor":
        return CourseService.list_professor_courses(user_id)

    raise PermissionError("Unauthorized role for course retrieval.")


def list_notes(user_id, role):

    return AcademicAssistantService.get_notes(
        user_id=user_id,
        role=role
    )


def list_assignments(course_id, user_id, role):

    return AssignmentService.list_course_assignments(
        course_id=course_id,
        user={
            "id": user_id,
            "role": role
        }
    )


def list_submissions(assignment_id, professor_id):

    return SubmissionService.get_assignment_submissions(
        assignment_id=assignment_id,
        professor_id=professor_id
    )


def list_milestones(project_id, user_id, role):

    return ProjectService.get_project_milestones(
        project_id=project_id,
        user_id=user_id,
        role=role
    )


def view_published_grades(user_id, student_id, role):

    if role != "student":
        raise PermissionError(
            "Only students can use this grade-viewing tool."
        )

    if user_id != student_id:
        raise PermissionError(
            "Students can only view their own grades."
        )

    return GradingService.get_student_grades(student_id)


def build_academic_tool_registry():

    registry = ToolRegistry()

    registry.register_tool(
        name="list_courses",
        description=(
            "Retrieve all courses associated with the authenticated "
            "student or professor. Does not require a course ID. "
            "For students, retrieve their enrolled courses."
        ),
        function=list_courses,
        required_parameters=["user_id", "role"]
    )

    registry.register_tool(
        name="list_notes",
        description="Retrieve notes accessible to a user.",
        function=list_notes,
        required_parameters=["user_id", "role"]
    )

    registry.register_tool(
        name="list_assignments",
        description="Retrieve assignments belonging to a course.",
        function=list_assignments,
        required_parameters=["course_id", "user_id", "role"]
    )

    registry.register_tool(
        name="list_submissions",
        description="Retrieve submissions for an assignment.",
        function=list_submissions,
        required_parameters=["assignment_id", "professor_id"]
    )

    registry.register_tool(
        name="list_milestones",
        description="Retrieve milestones associated with a project.",
        function=list_milestones,
        required_parameters=["project_id", "user_id", "role"]
    )

    registry.register_tool(
        name="view_published_grades",
        description="Retrieve a student's published grades.",
        function=view_published_grades,
        required_parameters=["user_id", "student_id", "role"]
    )

    return registry