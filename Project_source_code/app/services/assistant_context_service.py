from app.services.academic_assistant_service import AcademicAssistantService
from app.services.conversation_service import ConversationService


class AssistantContextService:

    @staticmethod
    def build_context(user_id, role, conversation_id=None):

        # Retrieve academic information
        academic_context = (
            AcademicAssistantService.get_academic_context(
                user_id, role
            )
        )

        # Retrieve previous conversation messages
        conversation_history = []

        if conversation_id is not None:
            conversation_history = (
                ConversationService.get_conversation_history(
                    user_id, conversation_id
                )
            )

        # Retrieve persistent memory for students
        student_memory = []

        if role == "student":
            student_memory = (
                ConversationService.get_student_memory(user_id)
            )

        return {
            "user": {
                "user_id": user_id,
                "role": role
            },
            "academic_context": academic_context,
            "conversation_history": conversation_history,
            "student_memory": student_memory
        }