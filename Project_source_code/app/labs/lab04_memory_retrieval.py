import json

from app.services.memory_retrieval_service import MemoryRetrievalService
from app.services.conversation_service import ConversationService


def run_lab():
    print("\n" + "=" * 65)
    print("       LAB 4 - MEMORY AND RETRIEVAL")
    print("=" * 65)

    user_id = int(input("\nEnter existing student user ID: "))
    role = input("Enter role (student/professor): ").strip().lower()

    query = input("\nEnter a query for memory retrieval: ").strip()

    conversation_input = input(
        "Enter conversation ID (press Enter to skip): "
    ).strip()

    conversation_id = int(conversation_input) if conversation_input else None

    print("\n[1] RETRIEVING EXISTING CONVERSATIONS")

    conversations = ConversationService.get_user_conversations(user_id)

    print("Conversations available:", len(conversations))

    if conversation_id is not None:
        print("\n[2] RETRIEVING SHORT-TERM MEMORY")

        history = ConversationService.get_conversation_history(
            user_id=user_id,
            conversation_id=conversation_id,
            limit=20
        )

        print("Messages retrieved:", len(history))

        for message in history:
            print(
                f"{message['sender']}: "
                f"{message['content'][:150]}"
            )
    else:
        print("\n[2] SHORT-TERM MEMORY SKIPPED")

    print("\n[3] BUILDING RETRIEVAL CONTEXT")

    context = MemoryRetrievalService.build_retrieval_context(
        user_id=user_id,
        role=role,
        query=query,
        conversation_id=conversation_id,
        top_k=5
    )

    retrieval = context["memory_retrieval"]

    print("\nRetrieval method:", retrieval["retrieval_method"])
    print("Stored memories:", retrieval["total_memories_available"])
    print("Relevant memories:", len(retrieval["relevant_memories"]))

    print("\n[4] RELEVANT LONG-TERM MEMORIES")

    for memory in retrieval["relevant_memories"]:
        print("\nMemory ID:", memory["id"])
        print("Type:", memory["memory_type"])
        print("Content:", memory["memory_content"])
        print("Relevance score:", memory["relevance_score"])
        print("Matched keywords:", memory["matched_keywords"])

    print("\n[5] COMPLETE RETRIEVAL CONTEXT")

    print(json.dumps(
        context,
        indent=4,
        ensure_ascii=False,
        default=str
    ))

    print("\n" + "=" * 65)
    print("       LAB 4 EXECUTION COMPLETED")
    print("=" * 65)


if __name__ == "__main__":
    try:
        run_lab()
    except Exception as error:
        print("\n[LAB 4 ERROR]", error)