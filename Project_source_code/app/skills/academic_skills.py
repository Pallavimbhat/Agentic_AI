from app.skills.base_skill import BaseSkill
from app.skills.skill_registry import SkillRegistry
from app.tools.academic_tools import build_academic_tool_registry


class AssignmentOverviewSkill(BaseSkill):

    def __init__(self, tool_registry):

        super().__init__(
            name="assignment_overview",
            description="Retrieves and summarizes assignments belonging to a course.",
            required_parameters=["course_id"]
        )

        self.tools = tool_registry

    def execute(self, context, parameters):

        if context.get("role") not in ("student", "professor"):
            raise PermissionError("Invalid academic role.")

        return self.tools.execute_tool(
            "list_assignments",
            {
                "course_id": parameters["course_id"],
                "user_id": context["user_id"],
                "role": context["role"]
            }
        )


class ProfessorSubmissionOverviewSkill(BaseSkill):

    def __init__(self, tool_registry):

        super().__init__(
            name="professor_submission_overview",
            description="Retrieves submissions for an assignment owned by a professor.",
            required_parameters=["assignment_id"]
        )

        self.tools = tool_registry

    def execute(self, context, parameters):

        if context.get("role") != "professor":
            raise PermissionError(
                "Only professors can access this skill."
            )

        return self.tools.execute_tool(
            "list_submissions",
            {
                "assignment_id": parameters["assignment_id"],
                "professor_id": context["user_id"]
            }
        )


class StudentGradeReviewSkill(BaseSkill):

    def __init__(self, tool_registry):

        super().__init__(
            name="student_grade_review",
            description="Retrieves the authenticated student's published grades."
        )

        self.tools = tool_registry

    def execute(self, context, parameters):

        if context.get("role") != "student":
            raise PermissionError(
                "Only students can access this skill."
            )

        return self.tools.execute_tool(
            "view_published_grades",
            {
                "user_id": context["user_id"],
                "student_id": context["user_id"],
                "role": context["role"]
            }
        )


def build_academic_skill_registry():

    tool_registry = build_academic_tool_registry()

    skill_registry = SkillRegistry()

    skill_registry.register(
        AssignmentOverviewSkill(tool_registry)
    )

    skill_registry.register(
        ProfessorSubmissionOverviewSkill(tool_registry)
    )

    skill_registry.register(
        StudentGradeReviewSkill(tool_registry)
    )

    return skill_registry