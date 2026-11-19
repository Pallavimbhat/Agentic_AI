from datetime import datetime, timezone

from course_organizer.agents.base_agent import BaseAgent


class MilestoneAgent(BaseAgent):
    """Tracks project milestones, deadlines, and progress."""

    def __init__(self, db=None):
        super().__init__("Project Milestone Tracking Agent", db)

    def create_milestone(
        self,
        course_id,
        title,
        description,
        deadline,
        created_by,
    ):
        try:
            if not title or not title.strip():
                return self.failure(
                    "create_milestone",
                    "Milestone title is required.",
                )

            milestone = self.db.create_milestone(
                course_id=course_id,
                title=title.strip(),
                description=description,
                deadline=deadline,
                created_by=created_by,
            )

            milestone_id = (
                milestone.get("id")
                if isinstance(milestone, dict)
                else None
            )

            self.log_action(
                action="create_milestone",
                entity_type="project_milestone",
                entity_id=milestone_id,
                actor_id=created_by,
                details=f"Created milestone: {title}",
            )

            return self.success(
                "create_milestone",
                "Milestone created successfully.",
                milestone,
            )

        except Exception as exc:
            return self.failure("create_milestone", str(exc))

    def list_milestones(self, course_id=None):
        try:
            milestones = self.db.list_milestones(course_id=course_id)

            return self.success(
                "list_milestones",
                "Milestones retrieved successfully.",
                milestones,
            )

        except Exception as exc:
            return self.failure("list_milestones", str(exc))

    def update_progress(
        self,
        milestone_id,
        progress,
        status=None,
    ):
        try:
            progress = int(progress)

            if not 0 <= progress <= 100:
                return self.failure(
                    "update_progress",
                    "Progress must be between 0 and 100.",
                )

            allowed_statuses = {
                "pending",
                "in_progress",
                "completed",
                "overdue",
            }

            if status is not None and status not in allowed_statuses:
                return self.failure(
                    "update_progress",
                    "Invalid milestone status.",
                )

            if status is None:
                if progress == 100:
                    status = "completed"
                elif progress > 0:
                    status = "in_progress"
                else:
                    status = "pending"

            result = self.db.update_milestone(
                milestone_id=milestone_id,
                progress=progress,
                status=status,
            )

            self.log_action(
                action="update_milestone_progress",
                entity_type="project_milestone",
                entity_id=milestone_id,
                details=f"Progress updated to {progress}%; status={status}.",
            )

            return self.success(
                "update_progress",
                "Milestone progress updated.",
                result,
            )

        except (TypeError, ValueError):
            return self.failure(
                "update_progress",
                "Progress must be a whole number between 0 and 100.",
            )
        except Exception as exc:
            return self.failure("update_progress", str(exc))

    def check_deadline(self, deadline):
        """Check a milestone deadline expressed as an ISO date or datetime."""
        try:
            parsed_deadline = datetime.fromisoformat(deadline)

            if len(deadline) == 10:
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
            is_overdue = (
                parsed_deadline.astimezone(timezone.utc) < now
            )

            return self.success(
                "check_deadline",
                "Milestone deadline checked.",
                {
                    "deadline": deadline,
                    "is_overdue": is_overdue,
                    "status": "overdue" if is_overdue else "upcoming",
                },
            )

        except (TypeError, ValueError):
            return self.failure(
                "check_deadline",
                "Provide a valid ISO date or datetime.",
            )