import unittest
from lab8.swarm import SwarmManager
class SwarmTests(unittest.TestCase):
    def test_parallel_agents(self):
        r=SwarmManager({"a":lambda t:1,"b":lambda t:2}).run("test")
        self.assertTrue(r["success"]); self.assertEqual(len(r["results"]),2)
    def test_agent_failure_is_reported(self):
        r=SwarmManager({"bad":lambda t:1/0}).run("test")
        self.assertFalse(r["success"])
if __name__ == "__main__": unittest.main()
