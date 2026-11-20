import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_mcp_client():

    print("\n" + "=" * 65)
    print("       ACADEMICFLOW MCP CLIENT")
    print("=" * 65)

    # Launch the MCP server as a separate process.
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "app.connectors.academic_mcp_server"
        ]
    )

    async with stdio_client(server_parameters) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize MCP connection.
            await session.initialize()

            print("\n[CONNECTED] MCP server connection established.")

            # Discover tools exposed by the MCP server.
            response = await session.list_tools()

            available_tools = response.tools

            print("\n[1] DISCOVERED MCP TOOLS")

            for index, tool in enumerate(available_tools, start=1):
                print(f"{index}. {tool.name}")
                print(f"   Description: {tool.description}")

            print("\n[2] SELECT AN MCP TOOL")

            print("1. List Notes")
            print("2. List Assignments")
            print("3. List Submissions")
            print("4. List Project Milestones")
            print("5. View Published Grades")

            choice = input("\nSelect tool (1-5): ").strip()

            if choice == "1":

                tool_name = "list_notes"

                user_id = int(input("Enter user ID: "))
                role = input("Enter role: ").strip().lower()

                arguments = {
                    "user_id": user_id,
                    "role": role
                }

            elif choice == "2":

                tool_name = "list_assignments"

                course_id = int(input("Enter course ID: "))
                user_id = int(input("Enter user ID: "))
                role = input("Enter role: ").strip().lower()

                arguments = {
                    "course_id": course_id,
                    "user_id": user_id,
                    "role": role
                }

            elif choice == "3":

                tool_name = "list_submissions"

                assignment_id = int(input("Enter assignment ID: "))
                professor_id = int(input("Enter professor ID: "))

                arguments = {
                    "assignment_id": assignment_id,
                    "professor_id": professor_id
                }

            elif choice == "4":

                tool_name = "list_milestones"

                project_id = int(input("Enter project ID: "))
                user_id = int(input("Enter user ID: "))
                role = input("Enter role: ").strip().lower()

                arguments = {
                    "project_id": project_id,
                    "user_id": user_id,
                    "role": role
                }

            elif choice == "5":

                tool_name = "view_published_grades"

                student_id = int(input("Enter student ID: "))
                role = input("Enter role: ").strip().lower()

                arguments = {
                    "user_id": student_id,
                    "student_id": student_id,
                    "role": role
                }

            else:
                raise ValueError("Invalid tool selection.")

            # Confirm the selected tool was discovered.
            discovered_names = {
                tool.name for tool in available_tools
            }

            if tool_name not in discovered_names:
                raise RuntimeError(
                    f"MCP tool not discovered: {tool_name}"
                )

            print("\n[3] INVOKING MCP TOOL")

            print("Selected tool:", tool_name)
            print("Arguments:", arguments)

            # Invoke the tool through the MCP protocol.
            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            print("\n[4] MCP TOOL RESPONSE")

            if result.isError:
                print("[TOOL ERROR]")

            for content in result.content:

                if hasattr(content, "text"):
                    print(content.text)
                else:
                    print(content)

            print("\n" + "=" * 65)
            print("       MCP CLIENT EXECUTION COMPLETED")
            print("=" * 65)


if __name__ == "__main__":

    try:
        asyncio.run(run_mcp_client())

    except Exception as error:
        print("\n[MCP CLIENT ERROR]", error)