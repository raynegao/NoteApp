import hashlib
import time
from argon2 import PasswordHasher


# Same simple measurement as the teacher's lab: 100,000 MD5 hashes, one Argon2 hash.
n = 100_000
start = time.perf_counter()
for _ in range(n):
    hashlib.md5(b"guess").hexdigest()
md5_rate = n / (time.perf_counter() - start)

ph = PasswordHasher()
start = time.perf_counter()
ph.hash("guess")
argon2_time = time.perf_counter() - start
argon2_rate = 1 / argon2_time

print("MD5 hashes measured:", n)
print(f"Argon2: {argon2_time * 1000:.3f} ms for one hash")
print(f"MD5: {md5_rate:.3f} guesses/sec; {md5_rate * 86400:.3f} guesses/day")
print(f"Argon2: {argon2_rate:.3f} guesses/sec; {argon2_rate * 86400:.3f} guesses/day")
print(f"Argon2 is {md5_rate / argon2_rate:.3f} times slower per guess")
print(f"Argon2 parameters: m={ph.memory_cost} KiB, t={ph.time_cost}, p={ph.parallelism}")
print("One local CPU run; the daily figures are estimates, not a 24-hour test.")
