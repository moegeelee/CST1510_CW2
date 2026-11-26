"""Run this week's registration and login checks with python -m unittest -v."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import auth


class AuthTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.users = Path(folder.name) / "DATA" / "users.txt"
        self.password = "practice123"

    def test_login_before_registration(self):
        ok, _ = auth.login_user("anna", self.password, self.users)
        self.assertFalse(ok)
        self.assertFalse(self.users.exists())

    def test_invalid_registration_leaves_no_file(self):
        invalid_inputs = [
            ("anna", "short"),
            ("   ", self.password),
            ("an,na", self.password),
        ]
        for name, password in invalid_inputs:
            with self.subTest(name=name, password_length=len(password)):
                ok, _ = auth.register_user(name, password, self.users)
                self.assertFalse(ok)
        self.assertFalse(self.users.exists())

    def test_registered_user_can_log_in(self):
        ok, _ = auth.register_user(" Anna ", self.password, self.users)
        self.assertTrue(ok)
        self.assertTrue(auth.user_exists("anna", self.users))
        ok, _ = auth.login_user("ANNA", self.password, self.users)
        self.assertTrue(ok)

    def test_duplicate_preserves_original_account(self):
        auth.register_user("anna", self.password, self.users)
        original = self.users.read_text()
        ok, _ = auth.register_user("Anna", "different123", self.users)
        self.assertFalse(ok)
        self.assertEqual(self.users.read_text(), original)

    def test_wrong_password_and_unknown_name_get_same_message(self):
        auth.register_user("anna", self.password, self.users)
        wrong_password = auth.login_user("anna", "different123", self.users)
        unknown_name = auth.login_user("alex", self.password, self.users)
        self.assertFalse(wrong_password[0])
        self.assertEqual(wrong_password, unknown_name)

    def test_same_password_has_a_different_hash_for_each_account(self):
        for name in ["anna", "alex"]:
            auth.register_user(name, self.password, self.users)
        contents = self.users.read_text()
        self.assertNotIn(self.password, contents)
        hashes = dict(line.split(",", 1) for line in contents.splitlines())
        self.assertNotEqual(hashes["anna"], hashes["alex"])
        for stored_hash in hashes.values():
            self.assertTrue(auth.is_valid_hash(self.password, stored_hash))


if __name__ == "__main__":
    unittest.main()
