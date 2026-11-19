# Class 11 — CSRF lab

**Name:** Haitian Gao (2023903116)

**Date:** 19 November 2026

We used our local NotesApp at `http://localhost:8080` (HTTP mode, as the lab
instructions expect). The attack page is served from a second site at
`http://localhost:9000` by `python3 -m http.server 9000`.

The one idea of the hour: after login, the browser attaches the session cookie
to **every** request to `localhost:8080` by itself. NotesApp only checked "is
the cookie valid?" — it never checked "did this request come from **my** form?"
So any page that makes the victim's browser send a `POST /grades` gets that
request accepted as the victim. That is cross-site request forgery (CSRF),
NotesApp flaw #11.

## 1. Break — the forged request is accepted

### 1.1 With curl, cookie only

Eve is a student. Her Mathematics grade (note 10) was `9.1`. A teacher logged
in with:

```text
curl -s -c teacher.jar -d "username=prof.turing&password=teach123" \
     http://localhost:8080/login -o /dev/null -w "teacher login: HTTP %{http_code}\n"
```

Then a "change grade" request with **only** the cookie — no form, no page, and
even claiming another origin:

```text
curl -s -b teacher.jar -H "Origin: http://evil.example" \
     -d "note_id=10&grade=20&comment=Perfect work." \
     http://localhost:8080/grades -o /dev/null -w "forged request: HTTP %{http_code}\n"
```

Result: `forged request: HTTP 302`, and Eve's dashboard showed `20.0` with
_"Perfect work."_. The server never asked where the request came from. A valid
cookie was enough.

### 1.2 For real, in a browser — zero clicks

We created `prize.html` **outside** the NotesApp clone (in
`../csrf-evil-site/`), a page with a hidden form that submits itself the moment
it opens:

```html
<!doctype html>
<html><body>
<h1>Eve's project page</h1>
<p>Loading…</p>
<form id="f" action="http://localhost:8080/grades" method="POST">
  <input type="hidden" name="note_id" value="10">
  <input type="hidden" name="grade"   value="19.5">
  <input type="hidden" name="comment" value="Changed by Eve's page.">
</form>
<script>document.getElementById("f").submit();</script>
</body></html>
```

Served at `http://localhost:9000/prize.html`. We logged in as `prof.turing` in
a normal browser, then opened the link. The teacher clicked **nothing** on
NotesApp. The page flashed, the browser landed on the NotesApp teacher page,
and the All grades table showed note 10 as `19.5`, _"Changed by Eve's page."_
(screenshot: `csrf-attack-browser-result.png`). The teacher's browser sent the
request and attached the teacher's cookie by itself.

## 2. The fix — a secret stamp on every real form

Three small pieces in `web/app.py` and the templates:

**One random secret per session.** `secrets.token_urlsafe(32)` stored in the
Flask session, exposed to templates as `csrf_token()`.

**Checked on every POST.** A `@app.before_request` hook refuses any
state-changing POST whose `csrf_token` field does not match the session token
(compared with `hmac.compare_digest`), aborting with `400`. The login form is
the only exemption. The check fails closed: a session with **no** token yet is
refused too (`not expected or ...`), so an empty-to-empty comparison can never
pass.

**Printed in every real form.** A hidden
`<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` as the
first line inside every `<form method="post" …>`: one in `teacher.html`
(grades) and three in `admin.html` (delete user, create user, ping).

`SameSite=Lax` is also set on the session cookie as defence in depth, but the
server no longer depends on it.

Why Eve's page cannot just copy the token: the token lives inside NotesApp's
HTML. Reading a response from `localhost:8080` is forbidden by the same-origin
policy — Eve's page can **send** requests, blind, but can never **read** the
answer.

## 3. Closed — the forged request is refused, the real form works

After the fix (rebuilt with `docker compose up -d --build`), we logged in again
and replayed the forged request:

```text
forged request: HTTP 400
```

No token, no write. Eve's grade was unchanged.

The real form path still works: a real teacher first loads `/teacher` (the page
prints the token), then submits it back:

```text
token: 2qVlJiStyQ1zcayg… (43 chars)
real form: HTTP 302
```

Eve's grade was saved back to `9.1`, _"Very strong final exam."_.

### Browser test

Logged in as `prof.turing` and opened `http://localhost:9000/prize.html` again:
the browser landed on **400 Bad Request — CSRF token missing or wrong**
(screenshot: `csrf-blocked-400.png`). Note 10 did not change.

Real use still works after the fix:

- [x] teacher saves a grade (browser, real form; value changed and restored)
- [x] admin adds a user (created test user `csrftest`)
- [x] admin delete (removed `csrftest` again)
- [x] admin ping (`127.0.0.1`, 0% packet loss)

## 4. Tests

The CSRF check broke the old tests that POST without a token — expected, and
the same thing happens to the class 9/10 curl commands. We updated
`web/tests/test_export_hmac.py` so its POSTs carry the session token, and added
`web/tests/test_csrf.py` (5 tests: no token, wrong token, fail-closed empty
session, real token flow via `/teacher`, login exemption).

```text
Ran 40 tests in 0.332s — OK
```

## The deeper lesson

A cookie proves _who_ the browser belongs to, not _what they meant_. For
anything that changes data, the server must also check intent: a secret that
only its own pages print. `SameSite=Lax` helps, but it is the browser's
seatbelt — the server must not depend on it.
