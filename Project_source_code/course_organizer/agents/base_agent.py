from datetime import datetime, timezone

from course_organizer.database.db_service import DatabaseService


class BaseAgent:
    """Base class shared by all Course Organizer agents."""

    def __init__(self, agent_name, db=None):
        self.agent_name = agent_name
        self.db = db if db is not None else DatabaseService()

    def success(self, action, message, data=None):
        """Build a standard successful response."""
        return {
            "success": True,
            "agent": self.agent_name,
            "action": action,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def failure(self, action, message):
        """Build a standard failure response."""
        return {
            "success": False,
            "agent": self.agent_name,
            "action": action,
            "message": message,
            "data": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def log_action(
        self,
        action,
        entity_type,
        entity_id=None,
        actor_id=None,
        outcome="success",
        details="",
    ):
        """Record an agent action in the database audit log."""
        self.db.log_action(
            actor_type="agent",
            actor_id=actor_id,
            agent_name=self.agent_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            outcome=outcome,
            details=details,
        )
