import io
import unittest
from unittest.mock import MagicMock, patch

import app as notesapp
import export_hmac
from comment_crypto import encrypt_comment


CSV_DATA = (
    'student,class,grade,comment\r\n'
    'alice,Security,14,"Good work, 继续加油\r\n# HMAC: ordinary comment"\r\n'
).encode("utf-8")


class ExportHMACTests(unittest.TestCase):
    def test_export_round_trip_with_multiline_unicode_comment(self):
        protected = export_hmac.add_export_hmac(CSV_DATA)
        self.assertTrue(protected.startswith(CSV_DATA + b"# HMAC: "))
        self.assertTrue(export_hmac.verify_export_hmac(protected))

    def test_changed_grade_is_rejected(self):
        protected = export_hmac.add_export_hmac(CSV_DATA)
        changed = protected.replace(b",14,", b",18,", 1)
        self.assertNotEqual(changed, protected)
        self.assertFalse(export_hmac.verify_export_hmac(changed))

    def test_changed_tag_and_wrong_key_are_rejected(self):
        protected = export_hmac.add_export_hmac(CSV_DATA)
        changed = bytearray(protected)
        changed[-3] = ord("0") if changed[-3] != ord("0") else ord("1")
        self.assertFalse(export_hmac.verify_export_hmac(bytes(changed)))
        with patch.object(export_hmac, "key", b"different-test-key-32-bytes-long!!"):
            self.assertFalse(export_hmac.verify_export_hmac(protected))

    def test_missing_truncated_or_appended_data_is_rejected(self):
        protected = export_hmac.add_export_hmac(CSV_DATA)
        for data in (b"", CSV_DATA, protected[:-1], protected[:-20],
                     protected + b"alice,Security,18,changed\r\n",
                     protected.replace(b"\r\n", b"\n"),
                     protected.replace(b"# HMAC: ", b"# HMAC: \xff", 1)):
            with self.subTest(data=data):
                self.assertFalse(export_hmac.verify_export_hmac(data))


class ExportRoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = notesapp.app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["role"] = "teacher"

    def test_export_keeps_csv_fields_and_decrypts_comments(self):
        conn = MagicMock()
        conn.cursor.return_value.fetchall.return_value = [{
            "student": "alice", "class": "Security", "grade": 14,
            "comment": encrypt_comment("Good work, 继续加油\r\n# HMAC: ordinary comment"),
        }]
        with patch.object(notesapp, "get_db", return_value=conn):
            response = self.client.get("/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith(CSV_DATA))
        self.assertTrue(export_hmac.verify_export_hmac(response.data))
        self.assertIn("attachment", response.headers["Content-Disposition"])

    def test_upload_accepts_original_and_rejects_changed_grade(self):
        original = export_hmac.add_export_hmac(CSV_DATA)
        for data, status, message in (
            (original, 200, b"CHECK PASSED"),
            (original.replace(b",14,", b",18,", 1), 400, b"CHECK FAILED"),
            (CSV_DATA, 400, b"CHECK FAILED"),
        ):
            with self.subTest(status=status, message=message):
                response = self.client.post(
                    "/verify-export", data={"file": (io.BytesIO(data), "grades.csv")},
                )
                self.assertEqual(response.status_code, status)
                self.assertIn(message, response.data)

    def test_missing_and_oversized_uploads(self):
        self.assertEqual(self.client.post("/verify-export").status_code, 400)
        response = self.client.post("/verify-export", data={
            "file": (io.BytesIO(b"x" * (1024 * 1024 + 1)), "too-big.csv"),
        })
        self.assertEqual(response.status_code, 413)

    def test_only_teachers_can_export_or_verify(self):
        for role in (None, "student", "admin"):
            with self.subTest(role=role):
                with self.client.session_transaction() as session:
                    session.clear()
                    if role:
                        session["user_id"] = 1
                        session["role"] = role
                for path in ("/export.csv", "/verify-export"):
                    self.assertEqual(self.client.get(path).status_code, 302)
                self.assertEqual(self.client.post("/verify-export").status_code, 302)


if __name__ == "__main__":
    unittest.main()
