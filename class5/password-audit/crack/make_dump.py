import hashlib


# These are the six made-up accounts from the lab, not a real database dump.
accounts = {
    "liwei": "123456",
    "sofia": "iloveyou",
    "tomk": "qwerty123",
    "aisha": "password1",
    "marie": "mariepw",
    "raj": "Gv7#pLm2!xQ",
}

with open("crack/leaked_users.txt", "w") as f:
    for username, password in accounts.items():
        digest = hashlib.md5(password.encode()).hexdigest()
        f.write(f"{username}:{digest}\n")

print("Wrote 6 synthetic accounts to crack/leaked_users.txt")
