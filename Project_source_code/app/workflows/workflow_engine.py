import json
from datetime import datetime
from collections import defaultdict, deque

from app.database.connection import get_connection


def serialize(data):
    return json.dumps(data, default=str, ensure_ascii=False)


class WorkflowNode:

    def __init__(
        self,
        name,
        agent_name,
        operation,
        handler,
        input_builder=None
    ):
        self.name = name
        self.agent_name = agent_name
        self.operation = operation
        self.handler = handler
        self.input_builder = input_builder or (
            lambda context: context
        )


class WorkflowGraph:

    def __init__(self, name):

        self.name = name
        self.nodes = {}
        self.edges = defaultdict(list)
        self.reverse_edges = defaultdict(list)

    def add_node(self, node):

        if node.name in self.nodes:
            raise ValueError(
                f"Duplicate workflow node: {node.name}"
            )

        self.nodes[node.name] = node

    def add_edge(self, source, destination):

        if source not in self.nodes:
            raise ValueError(
                f"Unknown source node: {source}"
            )

        if destination not in self.nodes:
            raise ValueError(
                f"Unknown destination node: {destination}"
            )

        if destination in self.edges[source]:
            raise ValueError(
                f"Duplicate edge: {source} -> {destination}"
            )

        self.edges[source].append(destination)
        self.reverse_edges[destination].append(source)

    def execution_order(self):

        indegree = {
            name: len(self.reverse_edges[name])
            for name in self.nodes
        }

        queue = deque(
            name
            for name, degree in indegree.items()
            if degree == 0
        )

        order = []

        while queue:

            current = queue.popleft()
            order.append(current)

            for neighbor in self.edges[current]:

                indegree[neighbor] -= 1

                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self.nodes):
            raise ValueError(
                "Workflow contains a cycle. "
                "A directed acyclic graph is required."
            )

        return order


class WorkflowRepository:

    @staticmethod
    def start_workflow(workflow_name, user_id):

        connection = get_connection()

        try:

            valid_user = None

            if user_id is not None:

                valid_user = connection.execute(
                    "SELECT id FROM users WHERE id = ?",
                    (user_id,)
                ).fetchone()

            triggered_by = (
                valid_user["id"] if valid_user else None
            )

            cursor = connection.execute(
                """
                INSERT INTO workflow_executions (
                    workflow_name,
                    triggered_by,
                    status
                )
                VALUES (?, ?, ?)
                """,
                (
                    workflow_name,
                    triggered_by,
                    "running"
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:
            connection.close()

    @staticmethod
    def start_node(
        execution_id,
        node,
        input_data
    ):

        connection = get_connection()

        try:

            cursor = connection.execute(
                """
                INSERT INTO workflow_nodes (
                    execution_id,
                    node_name,
                    agent_name,
                    operation,
                    status,
                    input_data,
                    started_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    node.name,
                    node.agent_name,
                    node.operation,
                    "running",
                    serialize(input_data),
                    datetime.now().isoformat()
                )
            )

            connection.commit()

            return cursor.lastrowid

        finally:
            connection.close()

    @staticmethod
    def complete_node(node_id, output_data):

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE workflow_nodes
                SET status = ?,
                    output_data = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    "completed",
                    serialize(output_data),
                    datetime.now().isoformat(),
                    node_id
                )
            )

            connection.commit()

        finally:
            connection.close()

    @staticmethod
    def fail_node(node_id, error):

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE workflow_nodes
                SET status = ?,
                    error_message = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    "failed",
                    str(error),
                    datetime.now().isoformat(),
                    node_id
                )
            )

            connection.commit()

        finally:
            connection.close()

    @staticmethod
    def skip_node(execution_id, node, reason):

        connection = get_connection()

        try:

            connection.execute(
                """
                INSERT INTO workflow_nodes (
                    execution_id,
                    node_name,
                    agent_name,
                    operation,
                    status,
                    error_message,
                    started_at,
                    completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution_id,
                    node.name,
                    node.agent_name,
                    node.operation,
                    "skipped",
                    reason,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                )
            )

            connection.commit()

        finally:
            connection.close()

    @staticmethod
    def complete_workflow(execution_id, status):

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE workflow_executions
                SET status = ?,
                    completed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    datetime.now().isoformat(),
                    execution_id
                )
            )

            connection.commit()

        finally:
            connection.close()


class WorkflowEngine:

    def execute(self, graph, initial_context):

        if not isinstance(initial_context, dict):
            raise ValueError(
                "Initial workflow context must be a dictionary."
            )

        order = graph.execution_order()

        user_id = initial_context.get("user_id")

        execution_id = WorkflowRepository.start_workflow(
            graph.name,
            user_id
        )

        results = {}
        node_status = {}

        print(f"\n[WORKFLOW STARTED] {graph.name}")
        print(f"[WORKFLOW ID] {execution_id}")

        workflow_failed = False

        for node_name in order:

            # Reset for every node.
            # Prevents accidentally updating a previous node.
            node_id = None

            node = graph.nodes[node_name]

            dependencies = graph.reverse_edges[node_name]

            failed_dependencies = [
                dependency
                for dependency in dependencies
                if node_status.get(dependency) != "completed"
            ]

            if failed_dependencies:

                reason = (
                    "Skipped because dependencies did not complete: "
                    + ", ".join(failed_dependencies)
                )

                WorkflowRepository.skip_node(
                    execution_id,
                    node,
                    reason
                )

                node_status[node_name] = "skipped"

                print(
                    f"[SKIPPED] {node_name}: {reason}"
                )

                continue

            context = {
                "initial_context": initial_context,
                "previous_results": results
            }

            try:

                node_input = node.input_builder(context)

                node_id = WorkflowRepository.start_node(
                    execution_id,
                    node,
                    node_input
                )

                print(
                    f"\n[EXECUTING NODE] {node_name}"
                )

                output = node.handler(node_input)

                if not isinstance(output, dict):
                    raise TypeError(
                        "Node handler must return a dictionary."
                    )

                # Check nested specialist execution status.
                specialist_result = (
                    output.get("output", {})
                    .get("agent_result", {})
                )

                if (
                    isinstance(specialist_result, dict)
                    and specialist_result.get("success") is False
                ):
                    raise RuntimeError(
                        specialist_result.get(
                            "error",
                            "Specialist agent execution failed."
                        )
                    )

                # Check outer agent execution status.
                if output.get("success") is False:

                    raise RuntimeError(
                        output.get(
                            "error",
                            "Agent execution failed."
                        )
                    )

                WorkflowRepository.complete_node(
                    node_id,
                    output
                )

                results[node_name] = output
                node_status[node_name] = "completed"

                print(
                    f"[NODE COMPLETED] {node_name}"
                )

            except Exception as error:

                workflow_failed = True
                node_status[node_name] = "failed"

                print(
                    f"[NODE FAILED] {node_name}: {error}"
                )

                # Update only the current node's record.
                if node_id is not None:

                    try:

                        WorkflowRepository.fail_node(
                            node_id,
                            error
                        )

                    except Exception as logging_error:

                        print(
                            "[NODE LOGGING ERROR] "
                            f"{logging_error}"
                        )

        final_status = (
            "failed" if workflow_failed else "completed"
        )

        WorkflowRepository.complete_workflow(
            execution_id,
            final_status
        )

        print(
            f"\n[WORKFLOW FINISHED] {final_status.upper()}"
        )

        return {
            "workflow_id": execution_id,
            "workflow_name": graph.name,
            "status": final_status,
            "execution_order": order,
            "node_status": node_status,
            "results": results
        }