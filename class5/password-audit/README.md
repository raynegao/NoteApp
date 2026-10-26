# Lab 2 NotesApp Password Audit

Haitian Gao (2023903116)

26 October 2026

Partner: 叶与陈 (2023901708)

## Finding 1 Stored passwords

The MD5 test used the six made-up accounts from the lab and the teacher's public
wordlist. This is separate from NotesApp, which originally stored plain passwords.

**Cracked: 4/6 accounts in 0.108 ms**, using 170 words. The cracked accounts were
liwei, sofia, tomk and aisha. Their passwords were common words in the list.
marie and raj did not fall: `mariepw` was absent from the list, and raj's password
was a random string. Passing this small wordlist does not prove a password is safe.

**Severity: High.** After a database leak, an attacker can try common passwords
offline very quickly. Unsalted MD5 also gives the same hash for equal passwords.

**Fix:** use Argon2id with a random salt for each password.

## Finding 2 The fix measured

Measured inside the local Python 3.11 Docker web container. As in the lab, the
test hashes 100,000 MD5 guesses and one Argon2 guess.

| Hash | Guesses per second | Estimated guesses per day |
| --- | ---: | ---: |
| MD5 | 3,549,466 | 306,673,883,590 |
| Argon2id | 25.515 | 2,204,517 |

Argon2 took **39.192 ms per hash**, about **139,112 times slower** in this run.
Its settings were 65,536 KiB memory, 3 iterations and parallelism 4. Daily figures
are the measured rates multiplied by 86,400, not a full-day test. Other hardware
and repeated runs will give different speeds.

**Verdict:** MD5 makes common passwords cheap to guess. Argon2 makes a large
search much more expensive, but weak passwords can still be guessed.

## NotesApp state

Alice's first correct HTTPS login upgraded her stored password to
`$argon2id$v=19$m=65536,t=3,p=4$...`. Logging out and back in worked, including
after restarting the web container. Wrong passwords were rejected.

The login checks an existing Argon2 hash with `verify()`. For an old plain
password, it compares once and saves `hash()` only after a correct login.
Other accounts will upgrade when they next log in. This run changed only Alice's
password value; the 60 grade/comment rows were unchanged.

## Code and results

- [MD5 sample dump](crack/make_dump.py), [dictionary attack](crack/crack.py) and
  [benchmark](benchmark.py)
- [Measured output](results.txt) and [application checks](checks.json)
- [Login code](../../web/app.py) is at `web/app.py` from the repository root.

From this directory, run `python3 crack/make_dump.py` and `python3 crack/crack.py`.
From the repository root, run the benchmark in the running container:

```sh
docker compose exec -T web python /host/class5/password-audit/benchmark.py
docker compose exec -T web python -m unittest discover -s tests -v
```

The 21 unit tests and the independent PostgreSQL checks passed. The username SQL
is unchanged, as requested by the teacher for a later class.

Source: [teacher's Lab 2](https://kristenpire.github.io/epita-security-labs/class5/password-audit/)
and [original wordlist](https://kristenpire.github.io/epita-security-labs/class5/assets/common-passwords.txt).
