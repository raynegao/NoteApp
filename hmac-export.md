# Protect the grades export with HMAC

Class 4 homework, completed on 21 October 2026.

Source: Class 4, slide footer **13 / 25** ([assignment screenshot](class4/assignment.png)). The example asks the server to detect a changed grade using an HMAC stored in the export. The slide does not specify a submission format or deadline.

## How it works

The existing `/export.csv` route still exports the student, class, grade and decrypted comment fields. It now encodes the CSV as UTF-8 and calls `add_export_hmac()` in [export_hmac.py](web/export_hmac.py). This uses Python's standard HMAC implementation with SHA-256 and a random 256-bit secret key.

The last line is metadata, rather than another grade record:

```text
student,class,grade,comment
alice,Security,14,Good work
# HMAC: <64 hexadecimal characters>
```

The example above illustrates the format. The actual exports use CRLF line endings. The HMAC covers all CSV bytes before the final metadata line, including the header, commas, quotes, comments and line endings. The metadata line itself is excluded.

`verify_export_hmac()` separates the last line, recomputes the tag with the server's key and compares the full tags using `hmac.compare_digest()`. A missing or malformed footer, changed content, appended data or changed tag fails verification. It also handles CSV comments containing quoted newlines or the text `# HMAC: `.

The teacher page links to `/verify-export`, where a teacher can upload an export of up to 1 MiB. A valid file returns `CHECK PASSED` and HTTP 200; a changed or unsigned file returns `CHECK FAILED` and HTTP 400. Verification does not import records or update the database.

## Key and startup

From the NotesApp directory:

```sh
python3 create_comment_key.py
python3 create_export_key.py
docker compose up -d --build
docker compose exec -T web python -m unittest discover -s tests -v
```

`create_export_key.py` adds `EXPORT_HMAC_KEY` to the local `.env` without replacing the existing comment key. Repeating it keeps the HMAC key. `.env` is Git-ignored and has mode 0600; the key is passed to the web container and is never included in a CSV or response. Keep it to verify earlier exports after a restart.

The HMAC key is separate from the AES-GCM comment key and the teaching app's JWT and session secrets. No new package is needed.

## Demonstrate the homework

Log in with the teacher test account from [README](README.md#test-accounts), export a class CSV, then open [the local verification page](http://127.0.0.1:8080/verify-export). Upload the original file and check that it passes. Change one grade while keeping the existing HMAC footer, then upload it again and check that it fails.

The following evidence is included in [class4/evidence](class4/evidence/):

- [grades_export.csv](class4/evidence/grades_export.csv): the actual 60-record export, accepted by the server.
- [grades_export_tampered.csv](class4/evidence/grades_export_tampered.csv): the same export with Alice's Computer Science grade changed from 10.5 to 18 and the original HMAC footer retained, rejected by the server.
- [original-passed.jpg](class4/evidence/original-passed.jpg) and [tampered-rejected.jpg](class4/evidence/tampered-rejected.jpg): the two results checked in local Chrome.

These files record the checks on my local instance using the course's sample data. On a fresh installation,
export a new CSV before testing it: a newly generated HMAC key will not validate
an export signed with my local key. Do not copy or share `.env` to reuse that key.

On 21 October 2026, all 14 tests passed: the 6 existing comment-encryption tests and 8 export/HMAC tests. They cover multiline Unicode comments, grade and tag changes, a wrong key, missing/truncated/appended data, line-ending changes, the actual Flask export response, upload validation and teacher-only access. The slide's 14-to-18 example is included in these tests; the actual database sample starts at 10.5.

Real HTTP checks passed for full and per-class exports, the original file, rejection of a changed grade, a missing tag and appended data. After restarting the web container, the same original file still passed and the modified file still failed. All fields of the 60 existing database note records remained unchanged.

## Scope

This checks the exact exported bytes. Opening and saving a CSV in another application can change its encoding or line endings and invalidate the tag even if visible values look the same. The HMAC does not encrypt grades or establish whether an otherwise valid old export is current. Existing course-app vulnerabilities and Project 1 files are outside this change.

Reference: [Python hmac documentation](https://docs.python.org/3/library/hmac.html).
