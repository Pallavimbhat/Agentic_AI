from app.agents.base_agent import BaseAgent
from app.services.assignment_service import AssignmentService


class AssignmentDistributionAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Assignment Distribution Agent",
            description=(
                "Creates, publishes and retrieves academic "
                "assignments for students and professors."
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

        # Retrieve assignments for a course
        if action == "list":

            course_id = input_data.get("course_id")

            if not course_id:
                raise ValueError("Course ID is required.")

            assignments = AssignmentService.list_course_assignments(
                course_id=course_id,
                user={
                    "id": user_id,
                    "role": role
                }
            )

            return {
                "action": "list",
                "course_id": course_id,
                "total_assignments": len(assignments),
                "assignments": assignments
            }

        # Create and publish an assignment
        elif action == "create":

            if role != "professor":
                raise PermissionError(
                    "Only professors can create assignments."
                )

            required_fields = [
                "course_id",
                "title",
                "description",
                "maximum_marks",
                "deadline"
            ]

            for field in required_fields:
                if input_data.get(field) is None:
                    raise ValueError(
                        f"Missing required field: {field}"
                    )

            assignment = AssignmentService.create_assignment(
                course_id=input_data["course_id"],
                title=input_data["title"],
                description=input_data["description"],
                instructions=input_data.get("instructions", ""),
                maximum_marks=input_data["maximum_marks"],
                deadline=input_data["deadline"],
                created_by=user_id,
                status=input_data.get("status", "published")
            )

            return {
                "action": "create",
                "message": "Assignment created successfully.",
                "assignment": assignment
            }

        else:
            raise ValueError(
                "Invalid action. Supported actions: list, create."
            )