import json
import tempfile
import unittest
from pathlib import Path

from course_organizer.database.db_service import DatabaseService, DATABASE_PATH
from course_organizer.agents.unified_agent import UnifiedAcademicAgent
import agentic_core.runtime as core_runtime


class UnifiedAssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        db_copy = Path(self.temp.name) / "course_organizer.db"
        import shutil
        shutil.copy2(DATABASE_PATH, db_copy)
        self.db = DatabaseService(db_copy)
        self.agent = UnifiedAcademicAgent(self.db)
        self.old_state = core_runtime.STATE_DB
        core_runtime.STATE_DB = Path(self.temp.name) / "agentic_state.sqlite3"

    def tearDown(self):
        core_runtime.STATE_DB = self.old_state
        self.temp.cleanup()

    def test_all_fourteen_capabilities_route_through_one_assistant(self):
        prompts = {
            1: "Compare a chatbot and an agent for finding courses",
            2: "Calculate 12 + 30",
            3: json.dumps({"action":"create","name":"upper_text","description":"Uppercase text","operation":"uppercase"}),
            4: "Remember that I prefer concise explanations",
            5: "List available connectors",
            6: "Show runtime events for calculating 25 + 17",
            7: json.dumps({"nodes":[{"id":"a","operation":"word_count","input":"hello world"},{"id":"b","operation":"uppercase","input":"agent","depends_on":["a"]}]}),
            8: "Run parallel specialist analysis on this text: student scores improved but one assignment failed",
            9: "Research artificial intelligence applications in education",
            10: "Analyse these cloud logs: INFO started\nERROR database connection timeout",
            11: "Generate an SDLC test plan for a library management system",
            12: json.dumps({"diagnosis":"A proposed configuration change","proposed_change":"Update the local setting","rollback_plan":"Restore previous setting","privacy_scrubbed":True,"estimated_cost":10,"budget":100}),
            13: "Analyse civil engineering sensor readings: crack_width_mm=0.5\ndisplacement_mm=12",
            14: "Create ticket for campus portal login failure",
        }
        for expected_lab, prompt in prompts.items():
            with self.subTest(lab=expected_lab):
                result = self.agent.run(1, "student", prompt)
                self.assertTrue(result["success"], result)
                self.assertEqual(result["selected_capability"]["lab"], expected_lab)
                self.assertTrue(result["trace"])
                self.assertEqual(result["trace"][0]["status"], "completed")


    def test_assistant_answers_topic_question_from_latest_enrolled_note_content(self):
        enrolled = self.db._fetch_all(
            "SELECT course_id FROM course_enrollments WHERE student_id=? LIMIT 1", (1,)
        )
        self.assertTrue(enrolled, "test student must have an enrolled course")
        course_id = enrolled[0]["course_id"]
        self.db.create_note(
            course_id,
            "Retrieval Augmented Generation Notes",
            "Retrieval augmented generation combines retrieval with language generation. "
            "A retriever selects relevant documents and the generator uses that evidence "
            "to produce a grounded answer.",
            created_by=2,
        )
        result = self.agent.run(1, "student", "Explain retrieval augmented generation from my notes")
        self.assertTrue(result["success"], result)
        self.assertIn("retrieval augmented generation", result["answer"].lower())
        self.assertIn("retriever selects relevant documents", result["answer"].lower())
        self.assertIn("notes", result["data"])

    def test_professor_assistant_can_retrieve_notes_assignments_and_submissions_together(self):
        result = self.agent.run(2, "professor", "Give me everything about course notes, assignments and submissions")
        self.assertTrue(result["success"], result)
        self.assertIn("notes", result["data"])
        self.assertIn("assignments", result["data"])
        self.assertIn("submissions", result["data"])

    def test_natural_language_average_is_calculated(self):
        result = self.agent.run(1, "student", "Calculate the average of 85, 90, 75 and 95")
        self.assertTrue(result["success"], result)
        self.assertEqual(result["selected_capability"]["lab"], 2)
        self.assertEqual(result["result"]["result"], 86.25)

    def test_academic_question_uses_academic_workflow_without_fake_labs(self):
        result = self.agent.run(1, "student", "Show my pending assignments with deadlines")
        self.assertTrue(result["success"])
        self.assertIn("assignments", result["data"])
        self.assertEqual(result["integrated_labs"]["L9"], "available_not_invoked")
        self.assertNotIn("extended_lab_outputs", result)

    def test_professor_can_use_same_assistant_entry_point(self):
        result = self.agent.run(2, "professor", "List my courses")
        self.assertTrue(result["success"])
        self.assertIn("courses", result["data"])

    def test_natural_language_chained_calculation(self):
        result = self.agent.run(2, "professor", "Calculate 125 multiplied by 48, then divide the result by 6.")
        self.assertTrue(result["success"], result)
        self.assertEqual(result["result"]["result"], 1000)

    def test_division_by_zero_is_a_controlled_error(self):
        result = self.agent.run(2, "professor", "Calculate 100 divided by zero.")
        self.assertFalse(result["success"])
        self.assertIn("division by zero is undefined", result["answer"])

    def test_student_password_hash_is_never_returned(self):
        result = self.agent.run(2, "professor", "List all student accounts")
        self.assertTrue(result["success"])
        serialized = json.dumps(result.get("data", {})).lower()
        self.assertNotIn("password_hash", serialized)
        self.assertNotIn("hashed_password", serialized)

    def test_single_assistant_runs_and_persists_all_fourteen_demo_labs(self):
        result = self.agent.run(2, "professor", "Run the 14-lab demonstration suite")
        self.assertTrue(result["success"], result)
        self.assertEqual(result["result"]["labs_covered"], 14)
        self.assertEqual(result["result"]["failed"], 0)
        labs = {step["lab"] for step in result["result"]["steps"]}
        self.assertEqual(labs, set(range(1, 15)))
        self.assertTrue(all(step["run_id"] for step in result["result"]["steps"]))


if __name__ == "__main__":
    unittest.main()
