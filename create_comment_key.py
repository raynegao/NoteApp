"""Create the local comment key once. Keep this key to read existing comments."""
import base64
import os
from pathlib import Path


env_file = Path(__file__).resolve().parent / ".env"
content = env_file.read_text() if env_file.exists() else ""
if any(line.startswith("COMMENT_KEY=") for line in content.splitlines()):
    print("COMMENT_KEY already exists; keeping it.")
else:
    key = base64.b64encode(os.urandom(32)).decode("ascii")
    fd = os.open(env_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "w") as output:
        if content and not content.endswith("\n"):
            output.write("\n")
        output.write("COMMENT_KEY=" + key + "\n")
    print("Created COMMENT_KEY in .env. Do not commit or lose this file.")
os.chmod(env_file, 0o600)
