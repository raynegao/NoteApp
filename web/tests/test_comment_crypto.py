import base64
import unittest
from unittest.mock import patch

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import comment_crypto as crypto


class CommentCryptoTests(unittest.TestCase):
    def test_round_trip(self):
        for text in ("Good work", "继续加油 — très bien", "", "gcm:ordinary text"):
            with self.subTest(text=text):
                self.assertEqual(crypto.decrypt_comment(crypto.encrypt_comment(text)), text)

    def test_null(self):
        self.assertIsNone(crypto.encrypt_comment(None))
        self.assertIsNone(crypto.decrypt_comment(None))

    def test_fresh_nonce(self):
        first = crypto.encrypt_comment("Good work")
        second = crypto.encrypt_comment("Good work")
        self.assertNotEqual(base64.b64decode(first[4:])[:12],
                            base64.b64decode(second[4:])[:12])

    def test_tampering_is_rejected(self):
        data = base64.b64decode(crypto.encrypt_comment("Good work")[4:])
        for index in (0, 12, len(data) - 1):  # nonce, ciphertext, tag
            changed = bytearray(data)
            changed[index] ^= 1
            value = "gcm:" + base64.b64encode(changed).decode("ascii")
            with self.subTest(index=index), self.assertRaises(InvalidTag):
                crypto.decrypt_comment(value)

    def test_wrong_key_is_rejected(self):
        value = crypto.encrypt_comment("Good work")
        with patch.object(crypto, "aes", AESGCM(AESGCM.generate_key(bit_length=256))):
            with self.assertRaises(InvalidTag):
                crypto.decrypt_comment(value)

    def test_invalid_format_is_rejected(self):
        for value in ("Good work", "gcm:!", "gcm:YWJj"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                crypto.decrypt_comment(value)


if __name__ == "__main__":
    unittest.main()
