from app.agents.base_agent import BaseAgent
from app.services.grading_service import GradingService


class GradingAssistanceAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Grading Assistance Agent",
            description=(
                "Records professor-reviewed grades, AI suggestions "
                "and feedback for student submissions."
            )
        )

    def execute(self, input_data):

        action = input_data.get("action")
        user_id = input_data.get("user_id")
        role = input_data.get("role")

        if role != "professor":
            raise PermissionError(
                "Only professors can grade submissions."
            )

        if not user_id:
            raise ValueError("Professor ID is required.")

        if action == "grade":

            required = [
                "submission_id",
                "final_marks",
                "professor_feedback"
            ]

            for field in required:
                if input_data.get(field) is None:
                    raise ValueError(
                        f"Missing required field: {field}"
                    )

            result = GradingService.grade_submission(
                submission_id=input_data["submission_id"],
                professor_id=user_id,
                final_marks=input_data["final_marks"],
                professor_feedback=input_data["professor_feedback"],
                suggested_marks=input_data.get("suggested_marks"),
                ai_feedback=input_data.get("ai_feedback")
            )

            return {
                "action": "grade",
                "message": "Grade recorded and awaiting approval.",
                "grade": result
            }

        else:
            raise ValueError(
                "Supported action: grade."
            )