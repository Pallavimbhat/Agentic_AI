import json

from app.agents.central_agent import CentralAgent

from app.workflows.workflow_engine import (
    WorkflowNode,
    WorkflowGraph,
    WorkflowEngine,
    WorkflowRepository
)


def build_academic_workflow():

    coordinator = CentralAgent()

    graph = WorkflowGraph(
        name="AcademicFlow Academic Information Workflow"
    )

    # Node 1: Retrieve academic notes.
    notes_node = WorkflowNode(
        name="notes_retrieval",
        agent_name="Notes Repository Agent",
        operation="retrieve_notes",

        handler=lambda data: coordinator.run({
            "task": "notes",
            **data
        }),

        input_builder=lambda context: {
            "user_id": context["initial_context"]["user_id"],
            "role": context["initial_context"]["role"]
        }
    )

    # Node 2: Retrieve course assignments.
    assignment_node = WorkflowNode(
        name="assignment_retrieval",
        agent_name="Assignment Distribution Agent",
        operation="list_assignments",

        handler=lambda data: coordinator.run({
            "task": "assignments",
            "action": "list",
            **data
        }),

        input_builder=lambda context: {
            "user_id": context["initial_context"]["user_id"],
            "role": context["initial_context"]["role"],
            "course_id": context["initial_context"]["course_id"]
        }
    )

    graph.add_node(notes_node)
    graph.add_node(assignment_node)

    # Assignment retrieval depends on successful notes retrieval.
    graph.add_edge(
        "notes_retrieval",
        "assignment_retrieval"
    )

    return graph


def run_lab():

    print("\n==============================================")
    print("        LAB 7 - AGENTIC NODE GRAPH")
    print("==============================================")

    graph = build_academic_workflow()

    print("\n[1] WORKFLOW NODES")

    for name, node in graph.nodes.items():

        print(f"\nNode: {name}")
        print(f"Agent: {node.agent_name}")
        print(f"Operation: {node.operation}")

    print("\n[2] WORKFLOW EDGES")

    for source, destinations in graph.edges.items():

        for destination in destinations:

            print(f"{source} ---> {destination}")

    print("\n[3] TOPOLOGICAL EXECUTION ORDER")

    print(" ---> ".join(graph.execution_order()))

    print("\n[4] EXECUTING WORKFLOW")

    initial_context = {
        "user_id": 1,
        "role": "professor",
        "course_id": 1
    }

    engine = WorkflowEngine()

    result = engine.execute(
        graph,
        initial_context
    )

    print("\n[5] FINAL WORKFLOW RESULT")

    print(json.dumps(
        result,
        indent=4,
        default=str
    ))

    print("\n[6] DATABASE VERIFICATION")

    from app.database.connection import get_connection

    connection = get_connection()

    try:

        workflow = connection.execute(
            """
            SELECT *
            FROM workflow_executions
            WHERE id = ?
            """,
            (result["workflow_id"],)
        ).fetchone()

        nodes = connection.execute(
            """
            SELECT *
            FROM workflow_nodes
            WHERE execution_id = ?
            ORDER BY id
            """,
            (result["workflow_id"],)
        ).fetchall()

        print("\nWorkflow Record:")
        print(json.dumps(
            dict(workflow),
            indent=4,
            default=str
        ))

        print("\nWorkflow Node Records:")

        for node in nodes:

            print(json.dumps(
                dict(node),
                indent=4,
                default=str
            ))

    finally:
        connection.close()

    print("\n==============================================")
    print("       LAB 7 EXECUTION COMPLETED")
    print("==============================================")


if __name__ == "__main__":
    run_lab()