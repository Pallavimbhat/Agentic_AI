from app.agents.base_agent import BaseAgent
from app.services.grading_service import GradingService


class GradePublishingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Grade Publishing Agent",
            description=(
                "Manages professor approval and publication "
                "of grades and retrieves published student grades."
            )
        )

    def execute(self, input_data):

        action = input_data.get("action")
        user_id = input_data.get("user_id")
        role = input_data.get("role")

        if not user_id:
            raise ValueError("User ID is required.")

        if action == "view":

            if role != "student":
                raise PermissionError(
                    "Only students can retrieve their published grades."
                )

            grades = GradingService.get_student_grades(
                student_id=user_id
            )

            return {
                "action": "view",
                "total_grades": len(grades),
                "grades": grades
            }

        if role != "professor":
            raise PermissionError(
                "Only professors can approve or publish grades."
            )

        grade_id = input_data.get("grade_id")

        if not grade_id:
            raise ValueError("Grade ID is required.")

        if action == "approve":

            result = GradingService.approve_grade(
                grade_id=grade_id,
                professor_id=user_id
            )

            return {
                "action": "approve",
                "result": result
            }

        elif action == "publish":

            result = GradingService.publish_grade(
                grade_id=grade_id,
                professor_id=user_id
            )

            return {
                "action": "publish",
                "result": result
            }

        else:
            raise ValueError(
                "Supported actions: approve, publish, view."
            )