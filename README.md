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

## Coursework through Class 4

| Task | Files |
| --- | --- |
| Class 2: NotesApp exploration and first threat model | [Class 2 report and evidence](class2/README.md) |
| Class 3: Caesar frequency analysis and ECB/GCM image comparison | [Class 3 scripts and results](class3/README.md) |
| Project 1: group threat model | [Group diagram and risk workbook](project1/README.md) |
| Class 3 homework: encrypted comments | [Implementation and checks](comment-encryption.md) |
| Class 4 homework: HMAC-signed grades export | [Implementation, screenshots and checks](hmac-export.md) |

The Class 2 report describes the original app at `1c83e42`. The separate
`project1/` folder keeps the group's later 16-flow model. The app code includes
the Class 3 comment encryption and Class 4 export HMAC homework.

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
