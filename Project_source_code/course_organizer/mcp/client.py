import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def main():
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "course_organizer.mcp.server"],
        cwd=str(PROJECT_ROOT),
        env=None,
    )

    print("Connecting to Course Organizer MCP server...")

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            print("\nMCP connection successful!")

            result = await session.list_tools()

            print("\nAvailable MCP tools:")
            for tool in result.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\nTesting dashboard_summary...")
            response = await session.call_tool(
                "dashboard_summary",
                arguments={}
            )

            for item in response.content:
                if hasattr(item, "text"):
                    print(item.text)

            print("\nMCP client test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())