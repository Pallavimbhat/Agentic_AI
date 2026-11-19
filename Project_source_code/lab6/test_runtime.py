import unittest
from lab6.runtime import AgentRuntime

class RuntimeTests(unittest.TestCase):
    def test_successful_lifecycle(self):
        runtime = AgentRuntime()
        result = runtime.execute("test", lambda: 42)
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], 42)
        self.assertEqual(result["status"], "completed")
    def test_failure_is_recorded(self):
        runtime = AgentRuntime()
        result = runtime.execute("fail", lambda: 1 / 0)
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "failed")

if __name__ == "__main__": unittest.main()
