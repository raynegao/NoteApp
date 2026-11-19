import unittest
from unittest.mock import MagicMock, patch

import app as notesapp


class CsrfProtectionTests(unittest.TestCase):
    def setUp(self):
        self.client = notesapp.app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["username"] = "prof.turing"
            session["role"] = "teacher"

    def test_post_without_token_is_refused(self):
        with patch.object(notesapp, "get_db", return_value=MagicMock()):
            response = self.client.post(
                "/grades",
                data={"note_id": "10", "grade": "20", "comment": "x"},
            )
        self.assertEqual(response.status_code, 400)

    def test_post_with_wrong_token_is_refused(self):
        with patch.object(notesapp, "get_db", return_value=MagicMock()):
            response = self.client.post(
                "/grades",
                data={"note_id": "10", "grade": "20", "comment": "x",
                      "csrf_token": "wrong-token"},
            )
        self.assertEqual(response.status_code, 400)

    def test_session_without_token_fails_closed(self):
        # A session with no token yet must be refused, not compared as "" == "".
        with self.client.session_transaction() as session:
            session.clear()
            session["user_id"] = 1
            session["role"] = "teacher"
        with patch.object(notesapp, "get_db", return_value=MagicMock()):
            response = self.client.post(
                "/grades",
                data={"note_id": "10", "grade": "20", "comment": "x"},
            )
        self.assertEqual(response.status_code, 400)

    def test_teacher_page_prints_token_and_accepts_it(self):
        page = self.client.get("/teacher")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'name="csrf_token"', page.data)
        with self.client.session_transaction() as session:
            token = session["csrf"]
        self.assertTrue(token)
        with patch.object(notesapp, "get_db", return_value=MagicMock()):
            response = self.client.post(
                "/grades",
                data={"note_id": "10", "grade": "9.1", "comment": "ok",
                      "csrf_token": token},
            )
        self.assertEqual(response.status_code, 302)

    def test_login_post_is_exempt(self):
        # /login must keep working without a token (unknown user -> 200 page).
        with patch.object(notesapp, "get_db", return_value=MagicMock()):
            response = self.client.post(
                "/login",
                data={"username": "nobody", "password": "nope"},
            )
        self.assertNotEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
