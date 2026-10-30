import base64
import hashlib
import hmac
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

import app as notesapp


class JWTTests(unittest.TestCase):
    def setUp(self):
        self.key = "class7-test-key-not-a-real-secret-0123456789"
        self.key_patch = patch.object(notesapp, "JWT_SECRET", self.key)
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.payload = {"user_id": 6, "username": "alice", "role": "student"}

    def token(self, header, payload=None, key=None):
        def encode(value):
            raw = json.dumps(value, separators=(",", ":")).encode()
            return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

        h = encode(header)
        p = encode(self.payload if payload is None else payload)
        signature = hmac.new(
            (self.key if key is None else key).encode(),
            f"{h}.{p}".encode(), hashlib.sha256,
        ).digest()
        return f"{h}.{p}." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()

    def test_issued_hs256_token_verifies(self):
        self.assertEqual(notesapp.verify_jwt(notesapp.make_jwt(self.payload)), self.payload)

    def test_none_token_is_rejected(self):
        token = self.token({"alg": "none"}).rsplit(".", 1)[0] + "."
        self.assertIsNone(notesapp.verify_jwt(token))

    def test_only_exact_hs256_is_allowed(self):
        for header in ({}, {"alg": "hs256"}, {"alg": "HS512"}, {"alg": "RS256"}, {"alg": "NONE"}):
            with self.subTest(header=header):
                self.assertIsNone(notesapp.verify_jwt(self.token(header)))

    def test_old_secret_signature_is_rejected(self):
        forged = dict(self.payload, role="teacher")
        self.assertIsNone(notesapp.verify_jwt(self.token({"alg": "HS256"}, forged, "s3cr3t")))

    def test_changed_payload_is_rejected(self):
        h, _, signature = notesapp.make_jwt(self.payload).split(".")
        _, changed_payload, _ = self.token({"alg": "HS256"}, dict(self.payload, role="teacher")).split(".")
        self.assertIsNone(notesapp.verify_jwt(f"{h}.{changed_payload}.{signature}"))

    def test_missing_or_wrong_signature_is_rejected(self):
        prefix = notesapp.make_jwt(self.payload).rsplit(".", 1)[0]
        for signature in ("", "wrong", "A" * 43):
            with self.subTest(signature=signature):
                self.assertIsNone(notesapp.verify_jwt(f"{prefix}.{signature}"))

    def test_bad_token_encoding_is_rejected(self):
        for token in (None, 42, "", "a.b", "a.b.c.d", "!!!.!!!.!!!", "e30.e30."):
            with self.subTest(token=token):
                self.assertIsNone(notesapp.verify_jwt(token))

    def test_header_and_payload_must_be_objects(self):
        for header, payload in (([], self.payload), ("HS256", self.payload), ({"alg": "HS256"}, [])):
            with self.subTest(header=header, payload=payload):
                self.assertIsNone(notesapp.verify_jwt(self.token(header, payload)))

    def test_non_ascii_signature_is_rejected(self):
        prefix = notesapp.make_jwt(self.payload).rsplit(".", 1)[0]
        self.assertIsNone(notesapp.verify_jwt(prefix + ".\u00e9"))

    def test_deeply_nested_json_is_rejected(self):
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        raw = ("[" * 2000 + "0" + "]" * 2000).encode()
        payload = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
        token = f"{header}.{payload}."
        self.assertIsNone(notesapp.verify_jwt(token))
        client = notesapp.app.test_client(use_cookies=False)
        response = client.get("/api/notes/3", headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 401)

    def test_forged_bearer_without_cookie_returns_401(self):
        client = notesapp.app.test_client(use_cookies=False)
        none = self.token({"alg": "none"}).rsplit(".", 1)[0] + "."
        old = self.token({"alg": "HS256"}, dict(self.payload, role="teacher"), "s3cr3t")
        malformed = self.token([], self.payload)
        for token in (none, old, malformed):
            with self.subTest(kind=token.split(".")[0]):
                with patch.object(notesapp, "get_db") as get_db:
                    response = client.get("/api/notes/3", headers={"Authorization": "Bearer " + token})
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.get_json(), {"error": "unauthorized"})
                get_db.assert_not_called()

    def test_valid_bearer_without_cookie_reaches_api(self):
        connection = MagicMock()
        connection.cursor.return_value.fetchone.return_value = {
            "id": 1, "student_id": 6, "class_id": 1, "grade": 14,
            "comment": None, "student": "alice", "class_name": "Maths",
        }
        client = notesapp.app.test_client(use_cookies=False)
        token = notesapp.make_jwt(self.payload)
        with patch.object(notesapp, "get_db", return_value=connection):
            response = client.get("/api/notes/1", headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["student"], "alice")

    def test_existing_session_authentication_is_preserved(self):
        with notesapp.app.test_request_context(headers={"Authorization": "Bearer invalid"}):
            notesapp.session["user_id"] = 6
            notesapp.session["username"] = "alice"
            notesapp.session["role"] = "student"
            self.assertEqual(notesapp.current_identity(), self.payload)

    def test_missing_secret_prevents_app_start(self):
        environment = os.environ.copy()
        environment.pop("JWT_SECRET", None)
        result = subprocess.run(
            [sys.executable, "-c", "import app"], env=environment,
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KeyError: 'JWT_SECRET'", result.stderr)


if __name__ == "__main__":
    unittest.main()
