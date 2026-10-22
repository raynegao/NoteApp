"""HMAC-SHA256 protection for a CSV export, including its exact line endings."""
import base64
import hashlib
import hmac
import os


key = base64.b64decode(os.environ["EXPORT_HMAC_KEY"], validate=True)
if len(key) != 32:
    raise ValueError("EXPORT_HMAC_KEY must be a Base64-encoded 32-byte key")


def add_export_hmac(csv_data):
    """Append a tag after the complete UTF-8 CSV, which ends with CRLF."""
    tag = hmac.new(key, csv_data, hashlib.sha256).hexdigest()
    return csv_data + b"# HMAC: " + tag.encode("ascii") + b"\r\n"


def verify_export_hmac(file_data):
    """Verify the CSV bytes before the final metadata line, not the tag itself."""
    csv_data, marker, footer = file_data.rpartition(b"# HMAC: ")
    if not marker or not csv_data.endswith(b"\r\n"):
        return False
    if len(footer) != 66 or not footer.endswith(b"\r\n"):
        return False
    expected = hmac.new(key, csv_data, hashlib.sha256).hexdigest().encode("ascii")
    return hmac.compare_digest(expected, footer[:-2])
