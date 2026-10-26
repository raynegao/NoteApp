import unittest
from unittest.mock import MagicMock, patch

import app as notesapp


class PasswordLoginTests(unittest.TestCase):
    def setUp(self):
        self.client = notesapp.app.test_client()
        self.conn = MagicMock()
        self.cur = self.conn.cursor.return_value

    def login(self, stored, password):
        self.cur.fetchone.return_value = {
            "id": 6, "username": "alice", "role": "student", "password": stored,
        }
        with patch.object(notesapp, "get_db", return_value=self.conn):
            return self.client.post("/login", data={
                "username": "alice", "password": password,
            })

    def test_correct_legacy_password_is_upgraded(self):
        response = self.login("alicepw", "alicepw")
        self.assertEqual(response.status_code, 302)
        sql, values = self.cur.execute.call_args.args
        self.assertEqual(sql, "UPDATE users SET password = %s WHERE id = %s")
        self.assertEqual(values[1], 6)
        self.assertTrue(values[0].startswith("$argon2id$"))
        self.assertTrue(notesapp.ph.verify(values[0], "alicepw"))
        with self.client.session_transaction() as session:
            self.assertEqual(session["user_id"], 6)

    def test_wrong_legacy_password_does_not_upgrade(self):
        response = self.login("alicepw", "wrong")
        self.assertIn(b"Invalid credentials.", response.data)
        self.assertEqual(self.cur.execute.call_count, 1)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_correct_argon2_password_logs_in_without_rewriting(self):
        stored = notesapp.ph.hash("alicepw")
        self.assertEqual(self.login(stored, "alicepw").status_code, 302)
        self.assertEqual(self.cur.execute.call_count, 1)
        with self.client.session_transaction() as session:
            self.assertEqual(session["username"], "alice")

    def test_wrong_argon2_password_is_rejected(self):
        response = self.login(notesapp.ph.hash("alicepw"), "wrong")
        self.assertIn(b"Invalid credentials.", response.data)
        self.assertEqual(self.cur.execute.call_count, 1)
        with self.client.session_transaction() as session:
            self.assertNotIn("user_id", session)

    def test_unknown_username_is_rejected(self):
        self.cur.fetchone.return_value = None
        with patch.object(notesapp, "get_db", return_value=self.conn):
            response = self.client.post("/login", data={
                "username": "missing", "password": "alicepw",
            })
        self.assertIn(b"Invalid credentials.", response.data)
        self.assertEqual(self.cur.execute.call_count, 1)

    def test_malformed_argon2_hash_is_rejected(self):
        for stored in ("$argon2", "$argon2id$broken"):
            with self.subTest(stored=stored):
                response = self.login(stored, "alicepw")
                self.assertIn(b"Invalid credentials.", response.data)

    def test_password_with_quote_is_not_put_in_select_query(self):
        response = self.login("alice'pw", "alice'pw")
        self.assertEqual(response.status_code, 302)
        query = self.cur.execute.call_args_list[0].args[0]
        self.assertNotIn("alice'pw", query)
        stored, user_id = self.cur.execute.call_args.args[1]
        self.assertTrue(notesapp.ph.verify(stored, "alice'pw"))


if __name__ == "__main__":
    unittest.main()
