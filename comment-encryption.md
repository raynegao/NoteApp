# Homework: Encrypt NotesApp comments

Source: Session 03, pages 25 and 30. The task is to use AES-GCM for the `notes.comment` column.

## How it works

I added two functions in [comment_crypto.py](web/comment_crypto.py):

- `encrypt_comment()` runs before an insert or update. It uses a 256-bit key and a new random 12-byte nonce for each comment.
- `decrypt_comment()` runs when the app reads comments for the student page, teacher page, JSON API or CSV export.

The database column is still TEXT. Its stored format is:

```text
gcm: + Base64(nonce + ciphertext + authentication tag)
```

The library adds the 16-byte tag automatically. A wrong key or a changed nonce, ciphertext or tag causes decryption to fail. Empty strings are encrypted too; SQL NULL stays NULL.

The key is saved in the local `.env` file and passed to the web container. It stays the same after a restart. `.env` is ignored by Git and must be kept to read existing comments. Running the key script again keeps the existing key.

## Run

From the NotesApp directory:

```sh
python3 create_comment_key.py
python3 create_export_key.py
docker compose up -d --build
docker compose exec -T web python -m unittest discover -s tests -v
```

[migrate_comments.py](web/migrate_comments.py) runs before the server starts. It encrypts old plaintext comments and checks comments that are already encrypted. It uses one transaction, so a failed check rolls back the migration. Running it again does not encrypt the same data twice.

## Checks completed

On 18 October 2026, all 60 existing comments were backed up locally, encrypted and decrypted back to exactly the original text. Grades and other note fields stayed unchanged. The private backup is in `local/comments-before-aes.json` and is ignored by Git.

Six unit tests passed. I also checked new and updated comments, Chinese text, empty strings, NULL, pages, API and CSV in a temporary test database. Tampering and a wrong key were rejected; a failed migration rolled back. After restarting the web container, the original comments were still readable.

This protects stored comments. The app still returns plaintext for display, and the course app's existing access-control problems remain. The original seed SQL contains the teacher's sample plaintext; startup migrates the database copies.

Reference: [cryptography AESGCM documentation](https://cryptography.io/en/latest/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM).
