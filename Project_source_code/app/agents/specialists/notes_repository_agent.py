from app.agents.base_agent import BaseAgent
from app.services.academic_assistant_service import AcademicAssistantService


class NotesRepositoryAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="Notes Repository Agent",
            description=(
                "Retrieves and searches academic notes "
                "while respecting student and professor permissions."
            )
        )

    def execute(self, input_data):

        user_id = input_data.get("user_id")
        role = input_data.get("role")
        query = input_data.get("query", "").strip().lower()

        if not user_id:
            raise ValueError("User ID is required.")

        if role not in ("student", "professor"):
            raise ValueError("Invalid user role.")

        # Retrieve role-accessible notes from the database
        notes = AcademicAssistantService.get_notes(
            user_id=user_id,
            role=role
        )

        # Filter notes if a search query is provided
        if query:
            notes = [
                note for note in notes
                if query in (note.get("title") or "").lower()
                or query in (note.get("description") or "").lower()
                or query in (note.get("course_name") or "").lower()
            ]

        return {
            "total_notes": len(notes),
            "search_query": query,
            "notes": notes,
            "access_role": role
        }