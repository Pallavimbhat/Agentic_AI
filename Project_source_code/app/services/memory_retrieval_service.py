import re

from app.services.assistant_context_service import AssistantContextService
from app.services.conversation_service import ConversationService


class MemoryRetrievalService:
    """
    Combines short-term conversation history, long-term student memory,
    and academic context using the existing database and services.
    """

    STOP_WORDS = {
        "the", "is", "am", "are", "was", "were", "a", "an", "and",
        "or", "to", "of", "in", "on", "for", "with", "my", "me",
        "i", "you", "your", "it", "this", "that", "what", "how",
        "can", "could", "would", "should", "please", "about"
    }

    @classmethod
    def _extract_keywords(cls, text):
        words = re.findall(r"[a-zA-Z0-9]+", str(text).lower())

        return {
            word for word in words
            if len(word) > 2 and word not in cls.STOP_WORDS
        }

    @classmethod
    def retrieve_relevant_memories(cls, memories, query, top_k=5):
        """
        Ranks existing memories using keyword overlap.
        Does not modify the database.
        """

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        query_keywords = cls._extract_keywords(query)

        if not query_keywords:
            return []

        ranked_memories = []

        for memory in memories:
            content = memory.get("memory_content", "")
            memory_keywords = cls._extract_keywords(content)

            overlap = query_keywords.intersection(memory_keywords)

            if overlap:
                ranked_memories.append({
                    **memory,
                    "relevance_score": len(overlap),
                    "matched_keywords": sorted(overlap)
                })

        ranked_memories.sort(
            key=lambda item: (
                -item["relevance_score"],
                -item.get("id", 0)
            )
        )

        return ranked_memories[:top_k]

    @classmethod
    def build_retrieval_context(
        cls,
        user_id,
        role,
        query,
        conversation_id=None,
        top_k=5
    ):
        """
        Builds a context package using existing academic and memory services.
        This method performs read-only retrieval.
        """

        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise ValueError("A valid user ID is required.")

        if role not in ("student", "professor"):
            raise ValueError("Invalid user role.")

        if not isinstance(query, str) or not query.strip():
            raise ValueError("A retrieval query is required.")

        if conversation_id is not None:
            if (
                not isinstance(conversation_id, int)
                or isinstance(conversation_id, bool)
                or conversation_id <= 0
            ):
                raise ValueError("Invalid conversation ID.")

        # Reuse the existing context-building implementation.
        context = AssistantContextService.build_context(
            user_id=user_id,
            role=role,
            conversation_id=conversation_id
        )

        # Retrieve relevant long-term memories.
        all_memories = context.get("student_memory", [])

        relevant_memories = cls.retrieve_relevant_memories(
            memories=all_memories,
            query=query,
            top_k=top_k
        )

        # Keep the complete academic context and conversation history.
        context["memory_retrieval"] = {
            "query": query,
            "retrieval_method": "Keyword Overlap",
            "total_memories_available": len(all_memories),
            "relevant_memories": relevant_memories
        }

        # Expose only retrieved memories as the focused memory context.
        context["relevant_student_memory"] = relevant_memories

        return context

    @staticmethod
    def save_long_term_memory(
        user_id,
        role,
        memory_type,
        memory_content
    ):
        """
        Explicitly saves a persistent student memory.
        This operation writes to the existing database.
        """

        if role != "student":
            raise PermissionError(
                "Only students can save student memories."
            )

        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise ValueError("A valid student ID is required.")

        return ConversationService.save_student_memory(
            student_id=user_id,
            memory_type=memory_type,
            memory_content=memory_content
        )