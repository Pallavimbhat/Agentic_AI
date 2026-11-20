import json

from app.agents.tool_using_agent import ToolUsingAgent


def run_lab():

    print("\n======================================")
    print(" LAB 2 - AI POWERED TOOL USING AGENT")
    print("======================================")

    agent = ToolUsingAgent()

    user_request = input(
        "\nEnter your academic request: "
    )

    user_id = int(input("Enter user ID: "))
    role = input("Enter role (student/professor): ").strip().lower()

    result = agent.run({
        "request": user_request,
        "user_id": user_id,
        "role": role
    })

    print("\n========== EXECUTION RESULT ==========")

    print(json.dumps(
        result,
        indent=4,
        default=str
    ))

    print("\n======================================")


if __name__ == "__main__":
    run_lab()