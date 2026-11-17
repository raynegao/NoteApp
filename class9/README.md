# Class 9 — Injection lab

**Name:** Haitian Gao (2023903116)

**Date:** 17 November 2026

We used our local NotesApp at `https://localhost:8443` (port 8080 redirects to
HTTPS in our setup).

The one idea of the hour: the server builds a *sentence* and hands it to an
interpreter — the database (its language is SQL) or the shell (its language is
OS commands) — by gluing our text straight into it. Our text was supposed to be
data, but because it is glued in, punctuation like `'`, `--` or `;` turns it
into part of the command. That is injection.

## 1. SQL injection — before the fix

The login query was built by string concatenation (`Flaw #8`):

```python
query = (
    "SELECT id, username, role, password FROM users "
    "WHERE username = '" + username + "'"
)
cur.execute(query)
```

Our Class 5 fix already verifies the password separately with Argon2, so the
classic payload can no longer skip the password check:

```
username = admin' --      password = anything
-> HTTP 200, "Invalid credentials."
```

The injected SQL still ran — the `'` closed the name blank and `--` commented
out the rest, so the admin row was reached — but Argon2 refused the junk
password. That is the Class 5 fix working as a second wall.

UNION, however, still broke in. A UNION row supplies its own id, role and
password column, so we logged in as admin without knowing `admin`'s password:

```
username = zzz' UNION SELECT 999, 'admin', 'admin', '<argon2 hash of "pwned123">' --
password = pwned123
-> HTTP 302 -> /, and GET /admin returns the full admin page
   (Users, Classes, prof.turing)
```

Go further — one UNION can also read the users table one row at a time. After
logging in with the subquery payload below, the Flask session cookie contained:

```
username = admin:$argon2id$v=19$m=65536,t=3,p=4$QI5Oj5tD9+k92fc/VBNFMA$U5KDMcMdx4L+C5RictUfFXfKOTQUPhKjnU0FBBMqnsg
```

That is the admin's stored password hash, leaked out of the database through
the login box.

## 2. Fix — un-glue the query

The fix is not banning quotes; it is stopping the gluing. We switched to a
parameterised query: a real blank (`%s`) that the database fills with our input
as data, never as grammar. The Class 5 Argon2 verification is kept as is.

The updated function in [web/app.py](../web/app.py#L144):

```python
        # Flaw #8 fix: parameterised query - input is data, never grammar.
        query = "SELECT id, username, role, password FROM users WHERE username = %s"
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(query, (username,))
            row = cur.fetchone()
```

After rebuilding, the exact same inputs now do nothing:

```
admin' --                                   -> HTTP 200, "Invalid credentials."
zzz' UNION SELECT 999, 'admin', 'admin', …  -> HTTP 200, "Invalid credentials."
zzz' UNION SELECT 999, (SELECT username…),… -> HTTP 200, "Invalid credentials."
```

`admin' --` is now a literal username that does not exist; the UNION payload is
one weird username string. The database never sees them as grammar.

## 3. Command injection — before the fix

The admin page has a "ping a host" box. The server glued the input into a shell
command (`Flaw #9`):

```python
cmd = "ping -c 1 " + host
subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
```

The shell obeys `;` as "now run the next command", so we put a second command
after the host:

```
host = 127.0.0.1; id; head -2 /etc/passwd
-> HTTP 200, page shows:

PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.124 ms

--- 127.0.0.1 ping statistics ---
1 packets transmitted, 1 received, 0% packet loss, time 0ms
rtt min/avg/max/mdev = 0.124/0.124/0.124/0.000 ms
uid=0(root) gid=0(root) groups=0(root)
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
```

The box was meant to ping a host; the `;` let us run arbitrary commands on the
server, as root, and read `/etc/passwd`.

## 4. Fix — no shell, a list of arguments

We stopped calling a shell at all: the command is handed over as a list of
arguments, so `host` is one single argument from start to finish and is never
re-read as syntax. As a second wall we also reject hosts that are not plain
hostnames or IPs.

The updated function in [web/app.py](../web/app.py#L370):

```python
    host = request.form.get("host", "")
    # Flaw #9 fix: no shell. host is one single argument, never re-read as syntax.
    if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
        output = "Invalid host: only letters, digits, dots and dashes are allowed."
    else:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", host],
                capture_output=True, text=True, timeout=10,
            )
            output = result.stdout + result.stderr
        except Exception as e:
            output = str(e)
```

The exact same input after the fix:

```
host = 127.0.0.1; id; head -2 /etc/passwd
-> HTTP 200: "Invalid host: only letters, digits, dots and dashes are allowed."
```

No command runs any more.

## 5. Real features still work

A fix that breaks the real login or the real ping is not a fix:

```
alice / alicepw           -> HTTP 302, dashboard shows "My grades"          OK
admin / admin123          -> HTTP 302, admin page opens                     OK
host = 127.0.0.1          -> normal ping output, 0% packet loss             OK
```

All 35 unit tests in `web/tests/` still pass after the fix.

## Hand-in

```
INJECTION FIX — NotesApp flaws #8 (SQL injection) and #9 (command injection) closed

  SQLi proof (break):   username  admin' --   -> HTTP 200 "Invalid credentials." — the
                        Class 5 Argon2 check caught the junk password; UNION still logged
                        us in as admin with an attacker-chosen password and no knowledge
                        of the real one (HTTP 302, /admin opens).
  SQLi fix:             login() uses a parameterised query (%s + tuple), no string gluing;
                        the Class 5 Argon2 verification is kept.
  SQLi proof (closed):  same UNION username now -> HTTP 200 "Invalid credentials.",
                        admin page blocked.

  CmdI proof (break):   host  127.0.0.1; id; head -2 /etc/passwd   returned ->
                        uid=0(root) gid=0(root) groups=0(root) and the first two lines
                        of /etc/passwd.
  CmdI fix:             admin_ping() uses subprocess.run(["ping","-c","1",host]) list,
                        no shell=True, plus a host format check.
  CmdI proof (closed):  same host now -> "Invalid host: only letters, digits, dots and
                        dashes are allowed."; no command output.

  Real use still works: alice login OK [x]   plain 127.0.0.1 ping OK [x]
```

## The deeper lesson

SQL and the shell were two languages, but one mistake: our text was glued into
a command string. The same bug waits anywhere text meets an interpreter — a
database, a shell, a web page (stored XSS, next class), a file path. The rule
is always the same: pass data as data, in its own envelope, never as part of
the command.
