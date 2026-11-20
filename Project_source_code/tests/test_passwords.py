import unittest

from app.security.passwords import (
    hash_password,
    verify_password
)


class TestPasswordSecurity(unittest.TestCase):

    def test_password_hashing(self):
        password = "Student@123"

        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(
            verify_password(password, hashed)
        )

    def test_wrong_password(self):
        hashed = hash_password("Student@123")

        self.assertFalse(
            verify_password("WrongPassword", hashed)
        )

    def test_different_salts(self):
        password = "Student@123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        self.assertNotEqual(hash1, hash2)

        self.assertTrue(
            verify_password(password, hash1)
        )

        self.assertTrue(
            verify_password(password, hash2)
        )

    def test_short_password(self):
        with self.assertRaises(ValueError):
            hash_password("123")


if __name__ == "__main__":
    unittest.main()