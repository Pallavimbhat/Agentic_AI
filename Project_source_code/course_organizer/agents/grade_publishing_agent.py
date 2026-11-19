from course_organizer.agents.base_agent import BaseAgent


class GradePublishingAgent(BaseAgent):
    """Approves and publishes grades with controlled access."""

    def __init__(self, db=None):
        super().__init__("Grade Publishing Agent", db)

    def approve_grade(self, grade_id, approved_by):
        """Approve a grade before publication."""
        try:
            if approved_by is None:
                return self.failure(
                    "approve_grade",
                    "An authorised approver is required.",
                )

            result = self.db.approve_grade(
                grade_id=grade_id,
                approved_by=approved_by,
            )

            self.log_action(
                action="approve_grade",
                entity_type="grade",
                entity_id=grade_id,
                actor_id=approved_by,
                details=f"Grade {grade_id} approval requested.",
            )

            return self.success(
                "approve_grade",
                "Grade approval processed.",
                result,
            )
        except Exception as exc:
            return self.failure("approve_grade", str(exc))

    def publish_grade(self, grade_id):
        """Publish only a grade that has been approved."""
        try:
            result = self.db.publish_grade(grade_id=grade_id)

            self.log_action(
                action="publish_grade",
                entity_type="grade",
                entity_id=grade_id,
                details=f"Grade {grade_id} publication requested.",
            )

            return self.success(
                "publish_grade",
                "Grade publication processed.",
                result,
            )
        except Exception as exc:
            return self.failure("publish_grade", str(exc))
