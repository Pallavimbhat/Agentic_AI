import unittest
from fastapi.testclient import TestClient
from course_organizer.main import app


class IntegratedApplicationTests(unittest.TestCase):
    def test_separate_lab_showcase_is_not_mounted(self):
        client = TestClient(app)
        self.assertEqual(client.get("/labs").status_code, 404)

    def test_student_sees_single_assistant_and_can_invoke_a_capability(self):
        client = TestClient(app)
        login = client.post("/login", data={"email":"test.student@example.com", "password":"student123"}, follow_redirects=False)
        self.assertEqual(login.status_code, 303)
        page = client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="integrated-assistant"', page.text)
        self.assertIn('id="assistantForm"', page.text)
        self.assertNotIn('lab-demo-btn', page.text)
        self.assertNotIn('runAllLabs', page.text)
        self.assertNotIn('labDemoPrompts', page.text)
        self.assertNotIn('Live Lab Demonstrations', page.text)
        self.assertNotIn('Open Lab Showcase', page.text)
        response = client.post("/api/assistant/query", json={"question":"Calculate 12 + 30"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["selected_capability"]["lab"], 2)

    def test_professor_can_use_same_assistant(self):
        client = TestClient(app)
        login = client.post("/login", data={"email":"test.professor@example.com", "password":"professor123"}, follow_redirects=False)
        self.assertEqual(login.status_code, 303)
        page = client.get("/")
        self.assertIn('id="integrated-assistant"', page.text)
        response = client.post("/api/assistant/query", json={"question":"List my courses"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])


if __name__ == "__main__":
    unittest.main()
