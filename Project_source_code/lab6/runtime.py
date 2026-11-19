"""Lab 6: lightweight agent runtime with lifecycle events and safe tool execution."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Any

@dataclass
class RuntimeEvent:
    timestamp: str
    event: str
    detail: str

@dataclass
class AgentRuntime:
    name: str = "Course Organizer Runtime"
    events: list[RuntimeEvent] = field(default_factory=list)
    status: str = "idle"

    def _log(self, event: str, detail: str):
        self.events.append(RuntimeEvent(datetime.now(timezone.utc).isoformat(), event, detail))

    def execute(self, task: str, action: Callable[[], Any]):
        if not task or not callable(action):
            raise ValueError("A task description and callable action are required")
        self.status = "running"
        self._log("started", task)
        try:
            result = action()
            self.status = "completed"
            self._log("completed", "Task executed successfully")
            return {"success": True, "task": task, "result": result, "status": self.status,
                    "events": [e.__dict__ for e in self.events]}
        except Exception as exc:
            self.status = "failed"
            self._log("failed", f"{type(exc).__name__}: {exc}")
            return {"success": False, "task": task, "error": str(exc), "status": self.status,
                    "events": [e.__dict__ for e in self.events]}
