from app.agents.base_agent import BaseAgent
from app.services.project_service import ProjectService


class ProjectMilestoneAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Project Milestone Tracking Agent",
            description=(
                "Creates, retrieves and updates project milestones "
                "for students and professors."
            )
        )

    def execute(self, input_data):

        action = input_data.get("action")
        user_id = input_data.get("user_id")
        role = input_data.get("role")

        if not user_id:
            raise ValueError("User ID is required.")

        if role not in ("student", "professor"):
            raise ValueError("Invalid user role.")

        if action == "create":

            if role != "professor":
                raise PermissionError(
                    "Only professors can create milestones."
                )

            required = ["project_id", "title"]

            for field in required:
                if not input_data.get(field):
                    raise ValueError(f"Missing field: {field}")

            result = ProjectService.create_milestone(
                professor_id=user_id,
                project_id=input_data["project_id"],
                title=input_data["title"],
                description=input_data.get("description"),
                deadline=input_data.get("deadline")
            )

            return {
                "action": "create",
                "result": result
            }

        elif action == "list":

            project_id = input_data.get("project_id")

            if not project_id:
                raise ValueError("Project ID is required.")

            result = ProjectService.get_project_milestones(
                project_id=project_id,
                user_id=user_id,
                role=role
            )

            return {
                "action": "list",
                "milestones": result
            }

        elif action == "update":

            if role != "student":
                raise PermissionError(
                    "Only students can update their milestone progress."
                )

            milestone_id = input_data.get("milestone_id")
            status = input_data.get("status")

            if not milestone_id or not status:
                raise ValueError(
                    "Milestone ID and status are required."
                )

            result = ProjectService.update_milestone(
                student_id=user_id,
                milestone_id=milestone_id,
                status=status
            )

            return {
                "action": "update",
                "result": result
            }

        else:
            raise ValueError(
                "Supported actions: create, list, update."
            )