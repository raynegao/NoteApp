"""Create the local CSV HMAC key once, keeping all existing keys."""
import base64
import os
from pathlib import Path


env_file = Path(__file__).resolve().parent / ".env"
content = env_file.read_text() if env_file.exists() else ""
existing = [line for line in content.splitlines() if line.startswith("EXPORT_HMAC_KEY=")]
if existing:
    key = base64.b64decode(existing[-1].split("=", 1)[1], validate=True)
    if len(existing) != 1 or len(key) != 32:
        raise ValueError("Keep exactly one valid 32-byte EXPORT_HMAC_KEY in .env")
    print("EXPORT_HMAC_KEY already exists; keeping it.")
else:
    key = base64.b64encode(os.urandom(32)).decode("ascii")
    fd = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "w") as output:
        if content and not content.endswith("\n"):
            output.write("\n")
        output.write("EXPORT_HMAC_KEY=" + key + "\n")
    print("Created EXPORT_HMAC_KEY in .env. Do not commit or lose this file.")
os.chmod(env_file, 0o600)
