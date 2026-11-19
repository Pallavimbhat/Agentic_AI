from lab7.graph import demo_graph
class GraphAgent:
    def run(self, request="Summarise my academic status"):
        return demo_graph_with_request(request)

def demo_graph_with_request(request):
    from lab7.graph import AgentGraph
    g=AgentGraph(); g.add_node("request", lambda c: c["request"])
    g.add_node("assignments", lambda c: {"pending": 2, "overdue": 0}, ["request"])
    g.add_node("notes", lambda c: ["AI fundamentals", "Search algorithms"], ["request"])
    g.add_node("summary", lambda c: {"assignment_data":c["assignments"],"notes":c["notes"]}, ["assignments","notes"])
    return g.run({"request":request})
