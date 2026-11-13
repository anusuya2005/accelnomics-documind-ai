import io

# If your main.py uses different URLs or field names, change ONLY this block.
LOGIN, LOGOUT, DOCS, ASK = "/api/auth/login", "/api/auth/logout", "/api/documents", "/api/ask"
PRIVACY, AUDIT = "/api/privacy/status", "/api/admin/audit"
FILE_FIELD, DEPT_FIELD = "file", "department_id"


def dept_id(db, name):
    return db.execute("SELECT id FROM departments WHERE name = ?", (name,)).fetchone()["id"]


def upload(client, headers, db, dept, filename, content, mime="text/plain"):
    return client.post(DOCS, headers=headers,
                       files={FILE_FIELD: (filename, io.BytesIO(content), mime)},
                       data={DEPT_FIELD: str(dept_id(db, dept))})


def upload_ok(client, headers, db, dept, filename, text):
    r = upload(client, headers, db, dept, filename, text.encode())
    assert r.status_code == 202, r.text
    return r.json()["id"]


def ask(client, headers, question):
    return client.post(ASK, headers=headers, json={"question": question})
