import shutil
import tempfile
import unittest
from pathlib import Path

from course_organizer.database.db_service import DatabaseService, DATABASE_PATH
from course_organizer.agents.integrated_lab_agent import IntegratedLabAgent
from course_organizer.agents.similarity_agent import SimilarityAgent


class IntegratedAssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "course_organizer.db"
        shutil.copy2(DATABASE_PATH, db_path)
        self.db = DatabaseService(db_path)
        self.agent = IntegratedLabAgent(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_queries_return_relevant_answers_and_truthful_trace(self):
        pending = self.agent.run(1, "Show my pending assignments with deadlines", "student")
        courses = self.agent.run(1, "Show my enrolled courses", "student")
        self.assertTrue(pending["success"])
        self.assertTrue(courses["success"])
        self.assertIn("pending/overdue", pending["answer"])
        self.assertIn("enrolled", courses["answer"])
        self.assertNotEqual(pending["answer"], courses["answer"])
        labs = {item["lab"] for item in pending["trace"] if "lab" in item}
        self.assertTrue({1, 2, 3, 4, 5, 6, 7, 8}.issubset(labs))
        self.assertEqual(set(pending["integrated_labs"][f"L{i}"] for i in range(1, 9)), {"executed"})
        self.assertEqual(set(pending["integrated_labs"][f"L{i}"] for i in range(9, 15)), {"available_not_invoked"})
        self.assertEqual(set(pending["data"].keys()), {"assignments"})

    def test_overview_answers_multiple_categories(self):
        result = self.agent.run(1, "Give me a complete academic overview", "student")
        self.assertEqual(set(result["intents"]), {"courses", "assignments", "submissions", "notes", "grades", "milestones"})
        self.assertIn("enrolled", result["answer"])
        self.assertIn("assignments", result["answer"])

    def test_memory_is_user_scoped_and_persistent(self):
        result = self.agent.run(1, "Remember that I prefer short study sessions", "student")
        self.assertIn("saved", result["answer"])
        recalled = self.agent.run(1, "What do you remember about my study preferences?", "student")
        self.assertIn("short study sessions", recalled["answer"])

    def test_75_question_bank_prompts_are_classified(self):
        import re
        bank = Path(__file__).resolve().parents[2] / "ACADEMIC_ASSISTANT_QUESTION_BANK.md"
        questions = re.findall(r"^\d+\. (.+)$", bank.read_text(encoding="utf-8"), re.M)
        self.assertEqual(len(questions), 75)
        for question in questions:
            with self.subTest(question=question):
                result = self.agent.run(1, question, "student")
                self.assertTrue(result["success"], result.get("answer"))
                self.assertEqual(set(result["integrated_labs"]), {f"L{i}" for i in range(1, 15)})
                self.assertEqual(set(result["integrated_labs"][f"L{i}"] for i in range(1, 9)), {"executed"})
                self.assertEqual(set(result["integrated_labs"][f"L{i}"] for i in range(9, 15)), {"available_not_invoked"})
                labs = {item["lab"] for item in result["trace"] if "lab" in item}
                self.assertTrue(labs.issubset(set(range(1, 9))))
                self.assertTrue(result["answer"].strip())

    def test_unsupported_question_does_not_claim_unrelated_labs_ran(self):
        result = self.agent.run(1, "Can you explain quantum mechanics?", "student")
        self.assertTrue(result["success"])
        self.assertEqual(set(result["integrated_labs"][f"L{i}"] for i in range(1, 9)), {"executed"})
        self.assertEqual(set(result["integrated_labs"][f"L{i}"] for i in range(9, 15)), {"available_not_invoked"})
        labs = {item["lab"] for item in result["trace"] if "lab" in item}
        self.assertTrue(labs.issubset(set(range(1, 9))))
        self.assertIn("couldn't match", result["answer"].lower())

    def test_similarity_comparison_creates_report_for_same_assignment(self):
        agent = SimilarityAgent(self.db)
        student = self.db.create_user("Similarity Test", "similarity.test@example.com", "student")
        second = self.db.submit_assignment(
            assignment_id=1, student_id=student["id"],
            content="This is another sample submission for the same assignment."
        )
        result = agent.compare_submissions(1, second["id"])
        self.assertTrue(result["success"], result)
        self.assertGreaterEqual(result["data"]["similarity_score"], 0)
        self.assertLessEqual(result["data"]["similarity_score"], 100)
        self.assertEqual(result["data"]["report"]["compared_submission_id"], second["id"])

    def test_similarity_rejects_submissions_from_different_assignments(self):
        agent = SimilarityAgent(self.db)
        result = agent.compare_submissions(1, 3)
        self.assertFalse(result["success"])
        self.assertIn("same assignment", result["message"])

    def test_similarity_rejects_same_submission_and_empty_text(self):
        agent = SimilarityAgent(self.db)
        same = agent.compare_submissions(1, 1)
        self.assertFalse(same["success"])
        with self.assertRaises(ValueError):
            agent._similarity("", "some submitted text")
        identical_score, _ = agent._similarity("same text in both submissions", "same text in both submissions")
        self.assertEqual(identical_score, 100.0)


if __name__ == "__main__":
    unittest.main()
