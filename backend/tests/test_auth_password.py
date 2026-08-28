import unittest
from unittest.mock import Mock

from app.api.v1.auth import ChangePasswordRequest, change_password
from app.models.user import User
from app.services.auth_service import hash_password, verify_password


class ChangePasswordTest(unittest.TestCase):
    def test_change_password_requires_current_password_and_updates_hash(self):
        user = User(username="tester", role="reviewer", hashed_password=hash_password("oldpass123"))
        db = Mock()

        result = change_password(
            ChangePasswordRequest(current_password="oldpass123", new_password="newpass456"),
            db,
            user,
        )

        self.assertEqual(result.code, 0)
        self.assertTrue(verify_password("newpass456", user.hashed_password))
        db.commit.assert_called_once()

    def test_change_password_rejects_wrong_current_password(self):
        user = User(username="tester", role="reviewer", hashed_password=hash_password("oldpass123"))
        db = Mock()

        result = change_password(
            ChangePasswordRequest(current_password="wrongpass", new_password="newpass456"),
            db,
            user,
        )

        self.assertEqual(result.code, 400)
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
