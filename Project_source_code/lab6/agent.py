"""Lab 6 runtime agent demo."""
from lab6.runtime import AgentRuntime
from lab6.execution_logger import ExecutionLogger

class RuntimeAgent:
    def __init__(self):
        self.runtime = AgentRuntime()
        self.logger = ExecutionLogger()

    def run(self, task="Demonstrate runtime lifecycle"):
        result = self.runtime.execute(task, lambda: {"message": "Runtime action completed", "task": task})
        self.logger.log({"lab": 6, "task": task, "status": result["status"]})
        result["audit_log"] = self.logger.read(5)
        return result
