import asyncio

from app.connectors.academic_mcp_client import run_mcp_client


def run_lab():

    print("\n" + "=" * 65)
    print("       LAB 5 - MCP CONNECTOR ARCHITECTURE")
    print("=" * 65)

    print("\nObjective:")
    print("Demonstrate MCP client-server communication.")

    print("\nArchitecture:")
    print("AcademicFlow Client")
    print("       |")
    print("       v")
    print("MCP Client")
    print("       |")
    print("       v")
    print("MCP Protocol")
    print("       |")
    print("       v")
    print("MCP Server")
    print("       |")
    print("       v")
    print("Academic Tool Registry")
    print("       |")
    print("       v")
    print("Existing Academic Services")
    print("       |")
    print("       v")
    print("Existing SQLite Database")

    print("\nStarting MCP communication...")

    asyncio.run(run_mcp_client())


if __name__ == "__main__":

    try:
        run_lab()

    except Exception as error:
        print("\n[LAB 5 ERROR]", error)