from app.agents.base_agent import BaseAgent
from app.services.submission_service import SubmissionService


class SubmissionCollectionAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Submission Collection Agent",
            description=(
                "Collects student assignment submissions, "
                "validates them and tracks submission status."
            )
        )

    def execute(self, input_data):

        action = input_data.get("action")
        user_id = input_data.get("user_id")
        role = input_data.get("role")

        if not user_id:
            raise ValueError("User ID is required.")

        if action == "submit":

            if role != "student":
                raise PermissionError(
                    "Only students can submit assignments."
                )

            required = ["assignment_id", "file_path"]

            for field in required:
                if not input_data.get(field):
                    raise ValueError(f"Missing field: {field}")

            result = SubmissionService.submit_assignment(
                assignment_id=input_data["assignment_id"],
                student_id=user_id,
                file_path=input_data["file_path"]
            )

            return {
                "action": "submit",
                "submission": result
            }

        elif action == "list":

            if role != "professor":
                raise PermissionError(
                    "Only professors can view assignment submissions."
                )

            assignment_id = input_data.get("assignment_id")

            if not assignment_id:
                raise ValueError("Assignment ID is required.")

            submissions = (
                SubmissionService.get_assignment_submissions(
                    assignment_id=assignment_id,
                    professor_id=user_id
                )
            )

            return {
                "action": "list",
                "total_submissions": len(submissions),
                "submissions": submissions
            }

        else:
            raise ValueError(
                "Supported actions: submit, list."
            )