import hashlib
import time


accounts = {}
with open("crack/leaked_users.txt") as f:
    for line in f:
        username, digest = line.strip().split(":")
        accounts[username] = digest

with open("crack/wordlist.txt") as f:
    wordlist = [line.strip() for line in f if line.strip()]

start = time.perf_counter()
cracked = {}
for candidate in wordlist:
    digest = hashlib.md5(candidate.encode()).hexdigest()
    for username, stored in accounts.items():
        if username not in cracked and stored == digest:
            cracked[username] = candidate
elapsed = time.perf_counter() - start

print(f"Wordlist: {len(wordlist)} entries")
print(f"Cracked {len(cracked)}/{len(accounts)} accounts in {elapsed * 1000:.3f} ms")
for username, password in cracked.items():
    print(f"{username}: {password}")
print("Not cracked:", ", ".join(u for u in accounts if u not in cracked))
