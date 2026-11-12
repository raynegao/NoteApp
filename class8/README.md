# Class 8 — IDOR lab

**Name:** Haitian Gao (2023903116)

**Date:** 12 November 2026

We used our local NotesApp at `https://localhost:8443`. Port 8080 redirects to
HTTPS in our setup.

## 1. Before the fix

Our prediction was that changing the id to 3 would return another student's
grade. The function checked whether we were logged in, but did not check who
owned the note.

Logged in as `alice`, we could read her notes 1 and 2, with grades 16.2 and 10.5.
Changing the URL to `/api/notes/3` returned HTTP 200 with Bob's grade, 12.6, and
the comment "Solid work, keep it up." Trying ids 1–15 returned all 15 notes.

This is IDOR: knowing a note id was enough to read it, even if it belonged to
someone else. Authentication worked, but the ownership check was missing.

## 2. Fix

We compared the note's `student_id` with the caller's `user_id`. If they differ,
the request is refused unless the caller is a teacher or admin. We chose 404
so a refused request gets the same response as a missing note.

The updated function in [web/app.py](../web/app.py#L221):

```python
@app.route("/api/notes/<int:note_id>")
def api_notes(note_id):
    ident = current_identity()
    if not ident:
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT n.id, n.student_id, n.class_id, n.grade, n.comment, "
        "u.username AS student, c.name AS class_name "
        "FROM notes n JOIN users u ON u.id = n.student_id "
        "JOIN classes c ON c.id = n.class_id WHERE n.id = %s",
        (note_id,),
    )
    note = cur.fetchone()
    conn.close()
    if not note:
        return jsonify({"error": "not found"}), 404
    # Flaw #7 fix (IDOR): you may only read your OWN note.
    # Teachers and admins may read any note; a student may not.
    # 404 (not 403) so callers cannot map which ids exist.
    if note["student_id"] != ident["user_id"] and ident.get("role") not in ("teacher", "admin"):
        return jsonify({"error": "not found"}), 404
    note["comment"] = decrypt_comment(note["comment"])
    note["grade"] = float(note["grade"]) if note["grade"] is not None else None
    return jsonify(note)
```

The code fix is committed as `181a853`.

## 3. Results after the fix

```
IDOR FIX — NotesApp flaw #7 (broken access control) closed
  Proof you got in:   as alice, /api/notes/3 returned bob's grade: 12.6 + "Solid work, keep it up."
  Fix:                api_notes refuses a note whose student_id is not the caller's,
                      unless the caller is a teacher/admin
  Code chosen:        returns [x] 404 not found   [ ] 403 forbidden
  Proof it's closed:  as alice, /api/notes/3 -> HTTP 404, {"error": "not found"}
                      as alice, /api/notes/1 -> HTTP 200, her own note (grade 16.2)
                      as prof.turing, /api/notes/3 -> HTTP 200, bob's note (grade 12.6)
```

We also tried the request without logging in and got HTTP 401
(`{"error": "unauthorized"}`). Repeating the scan from 1 to 15 as Alice only
returned her notes 1 and 2; ids 3–15 were refused.

Source: [Class 8 lab](https://kristenpire.github.io/epita-security-labs/class8/read-anyones-grade/).
