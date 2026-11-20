import json

from app.tools.academic_tools import build_academic_tool_registry


def run_lab():

    print("\n==========================================")
    print(" LAB 2 - TOOL USING AGENT")
    print("==========================================")

    registry = build_academic_tool_registry()

    print("\nREGISTERED TOOLS")

    for tool in registry.list_tools():
        print(json.dumps(tool, indent=4))

    tests = [
        (
            "NOTES RETRIEVAL",
            "list_notes",
            {
                "user_id": 1,
                "role": "professor"
            }
        ),
        (
            "ASSIGNMENT RETRIEVAL",
            "list_assignments",
            {
                "course_id": 1,
                "user_id": 1,
                "role": "professor"
            }
        ),
        (
            "SUBMISSION RETRIEVAL",
            "list_submissions",
            {
                "assignment_id": 1,
                "professor_id": 1
            }
        ),
        (
            "MILESTONE RETRIEVAL",
            "list_milestones",
            {
                "project_id": 1,
                "user_id": 1,
                "role": "professor"
            }
        ),
        (
            "GRADE RETRIEVAL",
            "view_published_grades",
            {
                "user_id": 3,
                "student_id": 3,
                "role": "student"
            }
        )
    ]

    for title, tool_name, arguments in tests:

        print(f"\n--- {title} ---")

        try:
            result = registry.execute_tool(
                tool_name,
                arguments
            )

            print("Tool:", tool_name)
            print("Status: SUCCESS")
            print(json.dumps(result, indent=4, default=str))

        except Exception as error:

            print("Status: FAILED")
            print("Error:", str(error))

    print("\n==========================================")
    print(" LAB 2 EXECUTION COMPLETED")
    print("==========================================")


if __name__ == "__main__":
    run_lab()