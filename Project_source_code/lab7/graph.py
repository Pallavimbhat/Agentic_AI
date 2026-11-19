"""Small dependency-aware workflow graph executor."""
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Node:
    name: str
    action: Callable[[dict], Any]
    depends_on: tuple = ()

class AgentGraph:
    def __init__(self): self.nodes = {}
    def add_node(self, name, action, depends_on=()):
        if name in self.nodes: raise ValueError(f"Duplicate node: {name}")
        self.nodes[name] = Node(name, action, tuple(depends_on))
    def run(self, initial=None):
        context = dict(initial or {})
        pending, completed, trace = set(self.nodes), set(), []
        while pending:
            ready = sorted(n for n in pending if set(self.nodes[n].depends_on) <= completed)
            if not ready: raise ValueError("Graph has missing dependencies or a cycle")
            for name in ready:
                node = self.nodes[name]
                missing = set(node.depends_on) - self.nodes.keys()
                if missing: raise ValueError(f"Node {name} has missing dependencies: {sorted(missing)}")
                try:
                    context[name] = node.action(context)
                    trace.append({"node": name, "status": "completed", "output": context[name]})
                except Exception as exc:
                    trace.append({"node": name, "status": "failed", "error": str(exc)})
                    return {"success": False, "context": context, "trace": trace}
                completed.add(name); pending.remove(name)
        return {"success": True, "context": context, "trace": trace}

def demo_graph():
    graph = AgentGraph()
    graph.add_node("request", lambda c: c.get("request", "Summarise my academic status"))
    graph.add_node("assignments", lambda c: {"pending": 2, "overdue": 0}, ["request"])
    graph.add_node("notes", lambda c: ["AI fundamentals", "Search algorithms"], ["request"])
    graph.add_node("summary", lambda c: {"request": c["request"], "assignment_data": c["assignments"], "notes": c["notes"]}, ["assignments", "notes"])
    return graph.run()
