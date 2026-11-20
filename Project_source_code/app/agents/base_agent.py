import time
import uuid

from datetime import datetime
from abc import ABC, abstractmethod

from app.services.agent_runtime_service import AgentRuntimeService


class BaseAgent(ABC):

    def __init__(self, name, description):

        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, input_data):
        pass

    def run(self, input_data):

        execution_uuid = str(uuid.uuid4())

        start_time = time.time()

        trace = []

        task = (
            input_data.get("task")
            or input_data.get("action")
            or input_data.get("operation")
            or "execute"
        )

        user_id = input_data.get("user_id")

        trace.append({
            "event": "AGENT_STARTED",
            "timestamp": datetime.now().isoformat(),
            "agent": self.name
        })

        database_execution_id = None

        try:

            # Register execution in the existing database.
            database_execution_id = (
                AgentRuntimeService.start_execution(
                    agent_name=self.name,
                    user_id=user_id,
                    task=task,
                    input_data=input_data
                )
            )

        except Exception as logging_error:

            trace.append({
                "event": "RUNTIME_LOGGING_WARNING",
                "timestamp": datetime.now().isoformat(),
                "error": str(logging_error)
            })

        try:

            output = self.execute(input_data)

            duration = round(time.time() - start_time, 4)

            trace.append({
                "event": "AGENT_COMPLETED",
                "timestamp": datetime.now().isoformat()
            })

            if database_execution_id is not None:

                try:

                    AgentRuntimeService.complete_execution(
                        execution_id=database_execution_id,
                        output_data=output,
                        duration=duration
                    )

                except Exception as logging_error:

                    trace.append({
                        "event": "RUNTIME_UPDATE_WARNING",
                        "error": str(logging_error)
                    })

            return {
                "success": True,
                "execution_id": execution_uuid,
                "database_execution_id": database_execution_id,
                "agent": self.name,
                "description": self.description,
                "status": "completed",
                "input": input_data,
                "output": output,
                "duration_seconds": duration,
                "execution_trace": trace
            }

        except Exception as error:

            duration = round(time.time() - start_time, 4)

            trace.append({
                "event": "AGENT_FAILED",
                "timestamp": datetime.now().isoformat(),
                "error": str(error)
            })

            if database_execution_id is not None:

                try:

                    AgentRuntimeService.fail_execution(
                        execution_id=database_execution_id,
                        error_message=error,
                        duration=duration
                    )

                except Exception as logging_error:

                    trace.append({
                        "event": "RUNTIME_UPDATE_WARNING",
                        "error": str(logging_error)
                    })

            return {
                "success": False,
                "execution_id": execution_uuid,
                "database_execution_id": database_execution_id,
                "agent": self.name,
                "status": "failed",
                "error": str(error),
                "duration_seconds": duration,
                "execution_trace": trace
            }