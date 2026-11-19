from course_organizer.agents.base_agent import BaseAgent


class SubmissionAgent(BaseAgent):
    """Manages student assignment submissions."""

    def __init__(self, db=None):
        super().__init__("Submission Collection Agent", db)

    def submit_assignment(
        self,
        assignment_id,
        student_id,
        content=None,
        file_path=None,
    ):
        try:
            if content is None and file_path is None:
                return self.failure(
                    "submit_assignment",
                    "Provide submission content or a file path.",
                )

            submission = self.db.submit_assignment(
                assignment_id=assignment_id,
                student_id=student_id,
                content=content,
                file_path=file_path,
            )

            submission_id = (
                submission.get("id")
                if isinstance(submission, dict)
                else None
            )

            self.log_action(
                action="submit_assignment",
                entity_type="submission",
                entity_id=submission_id,
                actor_id=student_id,
                details=f"Submission received for assignment {assignment_id}.",
            )

            return self.success(
                "submit_assignment",
                "Submission processed successfully.",
                submission,
            )

        except Exception as exc:
            return self.failure("submit_assignment", str(exc))

    def list_submissions(self, assignment_id):
        try:
            submissions = self.db.list_submissions(assignment_id)

            return self.success(
                "list_submissions",
                "Submissions retrieved successfully.",
                submissions,
            )

        except Exception as exc:
            return self.failure("list_submissions", str(exc))

    def get_submission(self, submission_id):
        try:
            submission = self.db.get_submission(submission_id)

            if not submission:
                return self.failure(
                    "get_submission",
                    "Submission not found.",
                )

            return self.success(
                "get_submission",
                "Submission retrieved successfully.",
                submission,
            )

        except Exception as exc:
            return self.failure("get_submission", str(exc))

    def update_status(self, submission_id, status):
        allowed_statuses = {
            "draft",
            "submitted",
            "late",
            "reviewed",
        }

        try:
            if status not in allowed_statuses:
                return self.failure(
                    "update_status",
                    f"Invalid status. Allowed values: {sorted(allowed_statuses)}",
                )

            result = self.db.update_submission_status(
                submission_id=submission_id,
                status=status,
            )

            self.log_action(
                action="update_submission_status",
                entity_type="submission",
                entity_id=submission_id,
                details=f"Submission status changed to {status}.",
            )

            return self.success(
                "update_status",
                "Submission status updated.",
                result,
            )

        except Exception as exc:
            return self.failure("update_status", str(exc))