
from app.database.connection import get_connection


class ConversationService:

    # --------------------------------------------------
    # 1. CREATE A NEW CONVERSATION
    # --------------------------------------------------

    @staticmethod
    def create_conversation(user_id, title="New Conversation"):

        conn = get_connection()

        try:
            cursor = conn.execute(
                """
                INSERT INTO conversations (user_id, title)
                VALUES (?, ?)
                """,
                (user_id, title)
            )

            conversation_id = cursor.lastrowid
            conn.commit()

            return {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": title
            }

        finally:
            conn.close()

    # --------------------------------------------------
    # 2. GET USER CONVERSATIONS
    # --------------------------------------------------

    @staticmethod
    def get_user_conversations(user_id):

        conn = get_connection()

        try:
            rows = conn.execute(
                """
                SELECT id, user_id, title, created_at
                FROM conversations
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,)
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            conn.close()

    # --------------------------------------------------
    # 3. VERIFY CONVERSATION OWNERSHIP
    # --------------------------------------------------

    @staticmethod
    def _verify_conversation(user_id, conversation_id, conn):

        conversation = conn.execute(
            """
            SELECT id, user_id, title
            FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, user_id)
        ).fetchone()

        if not conversation:
            raise ValueError(
                "Conversation not found or access denied."
            )

        return conversation

    # --------------------------------------------------
    # 4. SAVE A MESSAGE
    # --------------------------------------------------

    @classmethod
    def add_message(
        cls,
        user_id,
        conversation_id,
        sender,
        content,
        agent_name=None
    ):

        if sender not in ("user", "assistant", "agent"):
            raise ValueError("Invalid message sender.")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")

        conn = get_connection()

        try:
            cls._verify_conversation(
                user_id, conversation_id, conn
            )

            cursor = conn.execute(
                """
                INSERT INTO messages (
                    conversation_id,
                    sender,
                    content,
                    agent_name
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    sender,
                    content.strip(),
                    agent_name
                )
            )

            conn.commit()

            return {
                "message_id": cursor.lastrowid,
                "conversation_id": conversation_id,
                "sender": sender,
                "content": content.strip(),
                "agent_name": agent_name
            }

        finally:
            conn.close()

    # --------------------------------------------------
    # 5. RETRIEVE CONVERSATION HISTORY
    # --------------------------------------------------

    @classmethod
    def get_conversation_history(
        cls,
        user_id,
        conversation_id,
        limit=50
    ):

        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise ValueError("Limit must be between 1 and 200.")

        conn = get_connection()

        try:
            cls._verify_conversation(
                user_id, conversation_id, conn
            )

            rows = conn.execute(
                """
                SELECT id, conversation_id, sender,
                       content, agent_name, created_at
                FROM messages
                WHERE conversation_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (conversation_id, limit)
            ).fetchall()

            # Return messages in chronological order.
            return [dict(row) for row in reversed(rows)]

        finally:
            conn.close()

    # --------------------------------------------------
    # 6. UPDATE CONVERSATION TITLE
    # --------------------------------------------------

    @staticmethod
    def update_conversation_title(
        user_id,
        conversation_id,
        new_title
    ):

        if not new_title or not new_title.strip():
            raise ValueError("Conversation title cannot be empty.")

        conn = get_connection()

        try:
            cursor = conn.execute(
                """
                UPDATE conversations
                SET title = ?
                WHERE id = ? AND user_id = ?
                """,
                (
                    new_title.strip(),
                    conversation_id,
                    user_id
                )
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Conversation not found or access denied."
                )

            conn.commit()

            return {
                "conversation_id": conversation_id,
                "title": new_title.strip()
            }

        finally:
            conn.close()

    # --------------------------------------------------
    # 7. SAVE STUDENT MEMORY
    # --------------------------------------------------

    @staticmethod
    def save_student_memory(
        student_id,
        memory_type,
        memory_content
    ):

        if not memory_type or not memory_type.strip():
            raise ValueError("Memory type cannot be empty.")

        if not memory_content or not memory_content.strip():
            raise ValueError("Memory content cannot be empty.")

        conn = get_connection()

        try:
            cursor = conn.execute(
                """
                INSERT INTO student_memory (
                    student_id,
                    memory_type,
                    memory_content
                )
                VALUES (?, ?, ?)
                """,
                (
                    student_id,
                    memory_type.strip(),
                    memory_content.strip()
                )
            )

            memory_id = cursor.lastrowid
            conn.commit()

            return {
                "memory_id": memory_id,
                "student_id": student_id,
                "memory_type": memory_type.strip(),
                "memory_content": memory_content.strip()
            }

        finally:
            conn.close()

    # --------------------------------------------------
    # 8. RETRIEVE STUDENT MEMORY
    # --------------------------------------------------

    @staticmethod
    def get_student_memory(student_id, memory_type=None):

        conn = get_connection()

        try:
            if memory_type:
                rows = conn.execute(
                    """
                    SELECT id, student_id, memory_type,
                           memory_content, created_at, updated_at
                    FROM student_memory
                    WHERE student_id = ? AND memory_type = ?
                    ORDER BY updated_at DESC, id DESC
                    """,
                    (student_id, memory_type)
                ).fetchall()

            else:
                rows = conn.execute(
                    """
                    SELECT id, student_id, memory_type,
                           memory_content, created_at, updated_at
                    FROM student_memory
                    WHERE student_id = ?
                    ORDER BY updated_at DESC, id DESC
                    """,
                    (student_id,)
                ).fetchall()

            return [dict(row) for row in rows]

        finally:
            conn.close()

    # --------------------------------------------------
    # 9. DELETE A STUDENT MEMORY
    # --------------------------------------------------

    @staticmethod
    def delete_student_memory(student_id, memory_id):

        conn = get_connection()

        try:
            cursor = conn.execute(
                """
                DELETE FROM student_memory
                WHERE id = ? AND student_id = ?
                """,
                (memory_id, student_id)
            )

            if cursor.rowcount == 0:
                raise ValueError(
                    "Memory not found or access denied."
                )

            conn.commit()

            return {
                "message": "Student memory deleted successfully.",
                "memory_id": memory_id
            }

        finally:
            conn.close()