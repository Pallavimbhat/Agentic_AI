import unittest
import uuid

from app.security.auth import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_access_token,
    require_professor,
    require_student
)


class TestAuthentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        unique = uuid.uuid4().hex[:8]

        cls.professor_email = f"prof_{unique}@example.com"
        cls.student_email = f"student_{unique}@example.com"

        cls.professor = create_user(
            full_name="Test Professor",
            email=cls.professor_email,
            password="Professor@123",
            role="professor"
        )

        cls.student = create_user(
            full_name="Test Student",
            email=cls.student_email,
            password="Student@123",
            role="student"
        )

    def test_professor_account_creation(self):
        self.assertEqual(self.professor["role"], "professor")

    def test_student_account_creation(self):
        self.assertEqual(self.student["role"], "student")

    def test_duplicate_email_rejected(self):
        with self.assertRaises(ValueError):
            create_user(
                "Another Student",
                self.student_email,
                "Student@123",
                "student"
            )

    def test_successful_login(self):
        user = authenticate_user(
            self.student_email,
            "Student@123"
        )

        self.assertIsNotNone(user)

    def test_wrong_password_rejected(self):
        user = authenticate_user(
            self.student_email,
            "WrongPassword123"
        )

        self.assertIsNone(user)

    def test_jwt_generation(self):
        token = create_access_token(self.student)

        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

    def test_jwt_verification(self):
        token = create_access_token(self.student)

        user = verify_access_token(token)

        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "student")

    def test_invalid_token(self):
        user = verify_access_token("invalid.token.value")

        self.assertIsNone(user)

    def test_professor_permission(self):
        self.assertTrue(require_professor(self.professor))

    def test_student_permission(self):
        self.assertTrue(require_student(self.student))

    def test_student_cannot_use_professor_permission(self):
        with self.assertRaises(PermissionError):
            require_professor(self.student)

    def test_professor_cannot_use_student_permission(self):
        with self.assertRaises(PermissionError):
            require_student(self.professor)


if __name__ == "__main__":
    unittest.main()