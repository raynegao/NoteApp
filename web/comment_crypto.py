"""AES-GCM helpers for the notes.comment column."""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


key = base64.b64decode(os.environ["COMMENT_KEY"], validate=True)
if len(key) != 32:
    raise ValueError("COMMENT_KEY must be a Base64-encoded 32-byte key")
aes = AESGCM(key)
PREFIX = "gcm:"


def encrypt_comment(text):
    if text is None:
        return None
    nonce = os.urandom(12)
    ciphertext = aes.encrypt(nonce, text.encode("utf-8"), None)
    # AESGCM appends the authentication tag to the ciphertext.
    return PREFIX + base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_comment(value):
    if value is None:
        return None
    if not value.startswith(PREFIX):
        raise ValueError("Plaintext comment found; run migrate_comments.py first")
    data = base64.b64decode(value[len(PREFIX):], validate=True)
    if len(data) < 28:  # 12-byte nonce + at least a 16-byte tag
        raise ValueError("Invalid encrypted comment")
    return aes.decrypt(data[:12], data[12:], None).decode("utf-8")
