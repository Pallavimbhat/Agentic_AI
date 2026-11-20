import json

from app.agents.central_agent import CentralAgent
from app.services.agent_runtime_service import AgentRuntimeService


def run_lab():

    print("\n==============================================")
    print("          LAB 6 - AGENT RUNTIME")
    print("==============================================")

    coordinator = CentralAgent()

    print("\n[1] Registered Specialist Agents")

    for agent in coordinator.get_registered_agents():

        print(f"\nAgent: {agent['name']}")
        print(f"Description: {agent['description']}")

    print("\n[2] Executing Agent")

    request = {
        "task": "notes",
        "user_id": 1,
        "role": "professor"
    }

    result = coordinator.run(request)

    print("\n[EXECUTION RESULT]")

    print(json.dumps(
        result,
        indent=4,
        default=str
    ))

    print("\n[3] Recent Database Execution Logs")

    logs = AgentRuntimeService.get_recent_executions(limit=10)

    for log in logs:

        print("\n----------------------------------")

        print("Database Execution ID:", log["id"])
        print("Agent:", log["agent_name"])
        print("Task:", log["task"])
        print("Status:", log["status"])
        print("User ID:", log["user_id"])
        print("Duration:", log["duration"])
        print("Started:", log["started_at"])
        print("Completed:", log["completed_at"])

    print("\n==============================================")
    print("       LAB 6 EXECUTION COMPLETED")
    print("==============================================")


if __name__ == "__main__":
    run_lab()