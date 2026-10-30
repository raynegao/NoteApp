# Class 7 Login Fix

**Name:** Haitian Gao (2023903116)

**Partner:** Ye Yuchen (2023901708)

**Date:** 30 October 2026

## Fix

`verify_jwt` now accepts only exact `HS256` and checks the HMAC-SHA256 signature
with `hmac.compare_digest`. Unsigned and malformed tokens are rejected.

The old secret was replaced by a key generated from 32 random bytes.
`JWT_SECRET` is required through the environment, without a default. The real
key stays in the Git-ignored `.env`; Compose only contains its variable reference.
In production, use a secrets store rather than a committed secret.

Code: [app.py](../web/app.py), [Compose](../docker-compose.yml).

## Audit

LOGIN FIX — NotesApp flaw #4 (auth) closed.

| Check | Measured result |
| --- | --- |
| Unsigned `alg:none` token | HTTP 401, `unauthorized` |
| HS256 token signed with old `s3cr3t` key | HTTP 401, `unauthorized` |
| Real Alice login | HTTP 302, then dashboard HTTP 200 |
| Fresh Alice JWT, sent without cookies | HTTP 200 for her own grade |

The old-key forgery returned 200 before the final fix. All Bearer checks used
HTTPS with certificate verification and no cookies, avoiding session fallback.

All **35 tests passed**, including 14 JWT regression tests. Missing-key startup,
payload tampering and malformed-token rejection were checked. Database contents
and existing keys were unchanged during verification.

Source: [Class 7 lab](https://kristenpire.github.io/epita-security-labs/class7/fix-the-login/).
