import json

from mcp.server.fastmcp import FastMCP

from app.tools.academic_tools import build_academic_tool_registry


# Initialize MCP server
mcp = FastMCP("AcademicFlow MCP Server")

# Reuse the existing AcademicFlow Tool Registry
registry = build_academic_tool_registry()


def execute_academic_tool(tool_name, arguments):
    """
    Executes an existing AcademicFlow tool through the
    MCP server adapter.
    """

    result = registry.execute_tool(
        tool_name,
        arguments
    )

    return json.dumps(
        result,
        ensure_ascii=False,
        default=str
    )


@mcp.tool()
def list_notes(user_id: int, role: str) -> str:
    """Retrieve academic notes accessible to a user."""

    return execute_academic_tool(
        "list_notes",
        {
            "user_id": user_id,
            "role": role
        }
    )


@mcp.tool()
def list_assignments(
    course_id: int,
    user_id: int,
    role: str
) -> str:
    """Retrieve assignments belonging to a course."""

    return execute_academic_tool(
        "list_assignments",
        {
            "course_id": course_id,
            "user_id": user_id,
            "role": role
        }
    )


@mcp.tool()
def list_submissions(
    assignment_id: int,
    professor_id: int
) -> str:
    """Retrieve submissions for an assignment."""

    return execute_academic_tool(
        "list_submissions",
        {
            "assignment_id": assignment_id,
            "professor_id": professor_id
        }
    )


@mcp.tool()
def list_milestones(
    project_id: int,
    user_id: int,
    role: str
) -> str:
    """Retrieve milestones associated with an academic project."""

    return execute_academic_tool(
        "list_milestones",
        {
            "project_id": project_id,
            "user_id": user_id,
            "role": role
        }
    )


@mcp.tool()
def view_published_grades(
    user_id: int,
    student_id: int,
    role: str
) -> str:
    """Retrieve published grades belonging to a student."""

    return execute_academic_tool(
        "view_published_grades",
        {
            "user_id": user_id,
            "student_id": student_id,
            "role": role
        }
    )


if __name__ == "__main__":
    # MCP communicates over standard input/output.
    mcp.run(transport="stdio")