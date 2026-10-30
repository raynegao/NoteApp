# NotesApp

**Full name:** Haitian Gao

**Student ID:** 2023903116

A small grades application used throughout the Computer Security course. Teachers
record grades and comments for their classes, students read their own grades, and an
admin manages users and classes.

## Run it

You need Python 3 and a recent Docker Compose plugin with support for the
`!override` tag (Docker Desktop includes Compose).

```
git clone https://github.com/raynegao/NoteApp.git notesapp
cd notesapp
python3 create_comment_key.py
python3 create_export_key.py
python3 create_jwt_key.py
docker compose up -d --build
```

The first start builds the image, launches PostgreSQL, and loads the seed data
automatically. The comment encryption homework migrates stored comments before
the web server starts. Keep the local `.env` key file to read them after a restart.
When it is ready, open:

```
http://localhost:8080
```

## Test accounts

| Role    | Username      | Password   |
|---------|---------------|------------|
| Student | `alice`       | `alicepw`  |
| Teacher | `prof.turing` | `teach123` |
| Admin   | `admin`       | `admin123` |

(There are ~30 students in total; each student's password is their username + `pw`,
e.g. `bob` / `bobpw`.)

## Stack

- Python 3.11 + Flask (server-rendered Jinja2 pages and a small JSON API)
- PostgreSQL 15
- Docker Compose (`web` and `db` services)
- cryptography AES-GCM for stored comments
- argon2-cffi for password upgrades on login

## Coursework

| Task | Files |
| --- | --- |
| Class 2: NotesApp exploration and first threat model | [Class 2 report and evidence](class2/README.md) |
| Class 3: Caesar frequency analysis and ECB/GCM image comparison | [Class 3 scripts and results](class3/README.md) |
| Project 1: group threat model | [Group diagram and risk workbook](project1/README.md) |
| Class 3 homework: encrypted comments | [Implementation and checks](comment-encryption.md) |
| Class 4 homework: HMAC-signed grades export | [Implementation, screenshots and checks](hmac-export.md) |
| Class 5: HTTPS traffic audit | [Audit report and real screenshots](class5/README.md) |
| Class 5 Lab 2: password storage audit | [MD5 results, Argon2 measurement and login upgrade](class5/password-audit/README.md) |
| Class 6: forge a JWT token | [Finding, measured results and brute-force timing](class6/README.md) |
| Class 7: fix the login | [JWT fixes and audit results](class7/README.md) |

The Class 2 report describes the original app at `1c83e42`. The separate
`project1/` folder keeps the group's later 16-flow model. The app code includes
the Class 3 comment encryption, Class 4 export HMAC, Class 5 password homework
and Class 7 JWT verification fixes.

## Class 7 login fix

Run `python3 create_jwt_key.py` once before starting the app. It creates a random
JWT signing key in the Git-ignored `.env`, or keeps the existing key. Compose
passes it to the web container; the app has no weak default. Keep this key
separate from the comment encryption, export HMAC and Flask session keys.
After changing code or the JWT key, rebuild using the three-file HTTPS command
below. In production, supply secrets through a secrets store rather than a
committed file. See [the audit](class7/README.md) for the required checks.

## Class 5 password lab

The [short audit](class5/password-audit/README.md) records the synthetic MD5
dictionary attack, the measured MD5/Argon2 speeds and the login checks. Existing
plaintext passwords upgrade to Argon2id on the next correct login. Already
upgraded accounts use Argon2 verification. Rebuild the web image after pulling
these changes; in HTTPS mode keep all three Compose files:

```sh
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.https.yml up -d --build
```

The current suite has 35 tests. The original seed data and the later-class
username SQL exercise are unchanged.

## Comment encryption homework

See [the short homework explanation](comment-encryption.md) for the storage format,
key setup, migration and completed checks. Run the tests with:

```sh
docker compose exec -T web python -m unittest discover -s tests -v
```

## Grades export HMAC homework

Exports now include a final `# HMAC: ...` line using HMAC-SHA256. On the teacher
page, choose **Verify an exported CSV** to check a file. The original passes;
changing a grade while keeping the original tag fails. The separate secret key
is generated once by `python3 create_export_key.py` and kept in the Git-ignored
`.env`. See [the homework explanation and completed checks](hmac-export.md).

## Class 5 HTTPS lab

The [audit report](class5/README.md) includes the HTTP/HTTPS screenshots and
certificate comparison. The saved captures used cookie-free curl requests;
Chrome logins were additionally checked.

The HTTPS overlay adds Nginx and removes Flask's published host port. First
generate a local self-signed certificate if it does not already exist:

```sh
mkdir -p nginx/certs
if [ ! -e nginx/certs/notesapp.key ] && [ ! -e nginx/certs/notesapp.crt ]; then
  (umask 077; openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
    -keyout nginx/certs/notesapp.key -out nginx/certs/notesapp.crt \
    -subj '/CN=localhost' -addext 'subjectAltName=DNS:localhost,IP:127.0.0.1')
elif [ ! -s nginx/certs/notesapp.key ] || [ ! -s nginx/certs/notesapp.crt ]; then
  printf '%s\n' 'Incomplete certificate pair: restore the matching key and certificate before starting.' >&2
  false
fi
```

Keep all three Compose files so PostgreSQL stays on loopback port 5433:

```sh
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.https.yml up -d
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.https.yml exec -T nginx nginx -t
```

Open `https://localhost:8443`. The old `http://localhost:8080` entry redirects to
HTTPS. Both ports bind only to `127.0.0.1`. Inside Docker, Nginx listens on 80/443
and forwards to `web:5000`.

The self-signed certificate and private key are in the Git-ignored `nginx/certs/`.
Keep the private key local; do not add the certificate to system trust. For a
command-line check with certificate verification, use the exact local certificate:

```sh
curl --noproxy '*' --cacert nginx/certs/notesapp.crt https://localhost:8443/healthz
```

The report and evidence are in [class5/](class5/README.md). The existing 14 tests
and HTTPS export/HMAC checks passed; the database contents were unchanged.

To return to the plain-HTTP stack for another class exercise, stop the HTTPS
stack without deleting volumes, then start the usual stack:

```sh
docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.https.yml down
docker compose up -d
```

## Reset

```
docker compose down -v   # wipes the database volume
docker compose up        # reloads the seed data
```

## Updating your fork

The course repository is sometimes updated. Your fork does **not** update by itself.
To pull the latest changes into your fork:

**Easiest (GitHub website):** open your fork, and if it says *"This branch is behind
KristenPire/NoteApp"*, click **Sync fork → Update branch**. Then, in your local clone:

```
git pull
```

**Command line (keeps your own commits):**

```
git remote add upstream https://github.com/KristenPire/NoteApp.git   # once
git fetch upstream
git merge upstream/main
git push
```

Then **rebuild**, because the app code is baked into the Docker image:

```
docker compose up --build
```

A plain `docker compose up` would keep running the old image.
