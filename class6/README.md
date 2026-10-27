# Class 6 — Forge a token: become a teacher

Exercise on the local NotesApp clone (HTTPS mode, `https://localhost:8443`),
logged in as `alice` / `alicepw` (student). This exercise only breaks the app;
the fixes are kept for the next lab.

## Finding

```
FORGED-TOKEN FINDING — NotesApp flaw #4 (auth)
  What I read:   bob's grade (12.6) and comment ("Solid work, keep it up."), via /api/notes/3
  Break 1:       a JWT with "alg":"none" and no signature; role set to "teacher"
  Break 2:       cracked the HS256 secret (s3cr3t) from a wordlist; signed a real teacher token
  Why it worked: the server let the TOKEN choose how to verify, AND its secret was guessable
```

## Measured results

| Step | Request | Result |
| --- | --- | --- |
| Part 1 | `GET /api/notes/3` with no credentials | `HTTP 401` `{"error":"unauthorized"}` |
| Part 1 | `GET /api/notes/3` with `alg:none` token, empty signature, `role:teacher` | `HTTP 200`, bob's note returned |
| Part 2, Step 5 | Compare each word of the 15-word class wordlist against the HMAC-SHA256 signature of alice's real token | Secret cracked: `s3cr3t` |
| Part 2, Step 6 | `GET /api/notes/3` with an HS256 token signed with `s3cr3t` | `HTTP 200`, same note returned |

Bob's note (identical in both reads): `id=3, student=bob, class=Mathematics, grade=12.6, comment="Solid work, keep it up."`

## Record questions

- Payload role: `student`; the payload is Base64URL, not encrypted — a JWT hides
  nothing, the signature only proves it was not changed.
- Forged-token request returned bob's note (grade `12.6`), not an error.
- Signing secret: `s3cr3t`, a real leetspeak word present in the wordlist.
- A random 32-character secret would take about 36^32 ≈ 6.3e49 combinations;
  at this laptop's measured rate it would never finish in practice.
- The signed forged token worked (`HTTP 200`). Rejecting `alg:none` alone would
  not have stopped it, because its signature is real.

## Predictions (written before running)

- Part 1: `yes` — the server verifies however the token header says; a header of
  `none` skips signature verification. Confirmed by the `HTTP 200`.
- Part 2: `yes` — HS256 is only as strong as the secret; a short common word can
  be found by trying a wordlist. Confirmed by cracking `s3cr3t`.

## Brute-force timing (optional extension)

Measured on this laptop in pure Python, charset `a-z0-9` (36 characters):
~881,088 HMAC guesses/second.

| Length | Combos | Time |
| --- | --- | --- |
| 4 | 1,679,616 | 2 seconds |
| 5 | 60,466,176 | 69 seconds |
| 6 | 2,176,782,336 | 41 minutes (`s3cr3t` is here) |
| 7 | 78,364,164,096 | 24.7 hours |
| 8 | 2,821,109,907,456 | 37 days |
| 9 | 101,559,956,668,416 | 4 years |
| 10 | 3,656,158,440,062,976 | 132 years |
| 11 | 131,621,703,842,267,136 | 4,742 years |
| 12 | 4,738,381,338,321,616,896 | 170,726 years |

The wordlist wins in under a second because `s3cr3t` is a word. Against a long
**random** secret, neither the wordlist nor brute force ever finishes — that is
why the fix is "long AND random".

## Why it worked

1. **Blank-signature forgery (Part 1):** the server decides how to verify by
   reading the token's own header, and the header is written by the attacker.
   Setting `"alg":"none"` makes the server skip signature verification and trust
   the payload word for word, including `role:teacher`. No password, no key, no
   stolen cookie.
2. **Guessed secret (Part 2):** HS256 is just an HMAC; its strength is entirely
   the secret. The local secret `s3cr3t` is a common dictionary word, so it was
   recovered from a 15-word list in one pass. With the secret, anyone can sign a
   token the server cannot distinguish from its own.

## Side note (not fixed today)

The API also does not check note ownership: alice's browser session (a student)
could read `/api/notes/3` with her own cookie. Reading someone else's grade
therefore does not by itself prove the teacher role was enforced; the two issues
are kept separate in the finding above. Both are left for the next lab, which
rejects `alg:none`, pins the algorithm, and uses a long random secret.
