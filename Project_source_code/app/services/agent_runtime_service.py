import json
from datetime import datetime

from app.database.connection import get_connection


class AgentRuntimeService:

    @staticmethod
    def _serialize(data):
        return json.dumps(data, default=str, ensure_ascii=False)

    @staticmethod
    def _safe_input(input_data):
        allowed_fields = {
            "task",
            "action",
            "operation",
            "role",
            "user_id"
        }

        return {
            key: value
            for key, value in input_data.items()
            if key in allowed_fields
        }

    @staticmethod
    def _safe_output(output_data):
        if not isinstance(output_data, dict):
            return {"status": "completed"}

        allowed_fields = {
            "status",
            "success",
            "agent",
            "description",
            "selected_tool",
            "selection_reason"
        }

        return {
            key: value
            for key, value in output_data.items()
            if key in allowed_fields
        }

    @staticmethod
    def start_execution(agent_name, user_id, task, input_data):

        connection = get_connection()

        try:
            valid_user = None

            if user_id is not None:
                user = connection.execute(
                    "SELECT id FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()

                if user:
                    valid_user = user["id"]

            cursor = connection.execute(
                """
                INSERT INTO agent_executions (
                    agent_name,
                    user_id,
                    task,
                    status,
                    input_data
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    agent_name,
                    valid_user,
                    task,
                    "running",
                    AgentRuntimeService._serialize(
                        AgentRuntimeService._safe_input(input_data)
                    )
                )
            )

            connection.commit()
            return cursor.lastrowid

        finally:
            connection.close()

    @staticmethod
    def complete_execution(execution_id, output_data, duration):

        connection = get_connection()

        try:
            safe_output = AgentRuntimeService._safe_output(output_data)

            connection.execute(
                """
                UPDATE agent_executions
                SET status = ?,
                    output_data = ?,
                    duration = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    AgentRuntimeService._serialize(safe_output),
                    duration,
                    datetime.now().isoformat(),
                    execution_id
                )
            )

            connection.commit()

        finally:
            connection.close()

    @staticmethod
    def fail_execution(execution_id, error_message, duration):

        connection = get_connection()

        try:
            connection.execute(
                """
                UPDATE agent_executions
                SET status = ?,
                    error_message = ?,
                    duration = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    "Agent execution failed. Check application logs.",
                    duration,
                    datetime.now().isoformat(),
                    execution_id
                )
            )

            connection.commit()

        finally:
            connection.close()

    @staticmethod
    def get_recent_executions(limit=20):

        connection = get_connection()

        try:
            rows = connection.execute(
                """
                SELECT *
                FROM agent_executions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            connection.close()