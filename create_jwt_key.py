"""Create the local JWT key once, keeping all existing keys."""
import os
from pathlib import Path
import re
import secrets


env_file = Path(__file__).resolve().parent / ".env"
content = env_file.read_text() if env_file.exists() else ""
existing = re.findall(r"(?m)^\s*(?:export\s+)?JWT_SECRET\s*=\s*([^\r\n]*)", content)
if existing:
    value = existing[0].strip().strip("\"'")
    if len(existing) != 1 or len(value) < 43:
        raise ValueError("Keep exactly one long random JWT_SECRET in .env")
    print("JWT_SECRET already exists; keeping it.")
else:
    fd = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "w") as output:
        if content and not content.endswith("\n"):
            output.write("\n")
        output.write("JWT_SECRET=" + secrets.token_urlsafe(32) + "\n")
    print("Created JWT_SECRET in .env. Do not commit this file.")
os.chmod(env_file, 0o600)
