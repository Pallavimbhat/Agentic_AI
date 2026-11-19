import unittest
from lab7.graph import AgentGraph, demo_graph
class GraphTests(unittest.TestCase):
    def test_demo_graph(self): self.assertTrue(demo_graph()["success"])
    def test_cycle_detected(self):
        g=AgentGraph(); g.add_node("a",lambda c:1,["b"]); g.add_node("b",lambda c:2,["a"])
        with self.assertRaises(ValueError): g.run()
if __name__ == "__main__": unittest.main()
