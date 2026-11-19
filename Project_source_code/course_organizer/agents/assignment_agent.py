from datetime import datetime, timezone

from course_organizer.agents.base_agent import BaseAgent


class AssignmentAgent(BaseAgent):
    """Manages course assignments and their deadlines."""

    def __init__(self, db=None):
        super().__init__("Assignment Distribution Agent", db)

    def create_assignment(
        self,
        course_id,
        title,
        description,
        deadline,
        max_marks,
        created_by,
    ):
        try:
            if not title or not title.strip():
                return self.failure(
                    "create_assignment",
                    "Assignment title is required.",
                )

            if max_marks <= 0:
                return self.failure(
                    "create_assignment",
                    "Maximum marks must be greater than zero.",
                )

            assignment = self.db.create_assignment(
                course_id=course_id,
                title=title.strip(),
                description=description,
                deadline=deadline,
                max_marks=max_marks,
                created_by=created_by,
            )

            assignment_id = (
                assignment.get("id")
                if isinstance(assignment, dict)
                else None
            )

            self.log_action(
                action="create_assignment",
                entity_type="assignment",
                entity_id=assignment_id,
                actor_id=created_by,
                details=f"Created assignment: {title}",
            )

            return self.success(
                "create_assignment",
                "Assignment created successfully.",
                assignment,
            )

        except Exception as exc:
            return self.failure("create_assignment", str(exc))

    def list_assignments(self, course_id):
        try:
            assignments = self.db.list_assignments(course_id)

            return self.success(
                "list_assignments",
                "Assignments retrieved successfully.",
                assignments,
            )

        except Exception as exc:
            return self.failure("list_assignments", str(exc))

    def check_deadline(self, deadline):
        """Check whether an assignment deadline has passed.

        The deadline should be an ISO-format date or datetime string.
        Examples: 2026-12-31 or 2026-12-31T23:59:00+05:30
        """
        try:
            if not deadline:
                return self.failure(
                    "check_deadline",
                    "A deadline is required.",
                )

            deadline_text = deadline.strip()

            try:
                parsed_deadline = datetime.fromisoformat(deadline_text)
            except ValueError:
                return self.failure(
                    "check_deadline",
                    "Use an ISO-format date or datetime.",
                )

            if len(deadline_text) == 10:
                parsed_deadline = parsed_deadline.replace(
                    hour=23,
                    minute=59,
                    second=59,
                )

            if parsed_deadline.tzinfo is None:
                parsed_deadline = parsed_deadline.replace(
                    tzinfo=datetime.now().astimezone().tzinfo
                )

            now = datetime.now(timezone.utc)
            deadline_utc = parsed_deadline.astimezone(timezone.utc)
            is_overdue = now > deadline_utc

            return self.success(
                "check_deadline",
                "Deadline checked successfully.",
                {
                    "deadline": deadline_text,
                    "is_overdue": is_overdue,
                    "status": "overdue" if is_overdue else "upcoming",
                },
            )

        except Exception as exc:
            return self.failure("check_deadline", str(exc))