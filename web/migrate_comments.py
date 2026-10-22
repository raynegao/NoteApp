"""Encrypt old comments before the web server starts. Safe to run again."""
from app import get_db
from comment_crypto import PREFIX, decrypt_comment, encrypt_comment


def migrate_comments():
    conn = get_db()
    conn.autocommit = False
    changed = 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, comment FROM notes ORDER BY id FOR UPDATE")
            for row in cur.fetchall():
                value = row["comment"]
                if value is None:
                    continue
                if value.startswith(PREFIX):
                    decrypt_comment(value)  # Check the key and tag before skipping.
                else:
                    cur.execute("UPDATE notes SET comment = %s WHERE id = %s",
                                (encrypt_comment(value), row["id"]))
                    changed += 1
        conn.commit()
        return changed
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"Encrypted {migrate_comments()} old comments.")
