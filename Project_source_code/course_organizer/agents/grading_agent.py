from course_organizer.agents.base_agent import BaseAgent


class GradingAgent(BaseAgent):
    """Assists with grading and feedback."""

    def __init__(self, db=None):
        super().__init__("Grading Assistance Agent", db)

    def create_or_update_grade(
        self,
        submission_id,
        marks,
        feedback,
        graded_by,
    ):
        try:
            if marks is None or marks < 0:
                return self.failure(
                    "create_or_update_grade",
                    "Marks cannot be negative or empty.",
                )

            grade = self.db.create_or_update_grade(
                submission_id=submission_id,
                marks=marks,
                feedback=feedback,
                graded_by=graded_by,
            )

            self.log_action(
                action="create_or_update_grade",
                entity_type="grade",
                actor_id=graded_by,
                details=f"Grade prepared for submission {submission_id}.",
            )

            return self.success(
                "create_or_update_grade",
                "Grade saved for review. Approval is still required.",
                grade,
            )

        except Exception as exc:
            return self.failure("create_or_update_grade", str(exc))

    def get_grade(self, submission_id):
        try:
            grade = self.db.get_grade(submission_id)

            if not grade:
                return self.failure("get_grade", "Grade not found.")

            return self.success(
                "get_grade",
                "Grade retrieved successfully.",
                grade,
            )

        except Exception as exc:
            return self.failure("get_grade", str(exc))

    def list_grades(self, status=None):
        try:
            grades = self.db.list_grades(status=status)

            return self.success(
                "list_grades",
                "Grades retrieved successfully.",
                grades,
            )

        except Exception as exc:
            return self.failure("list_grades", str(exc))