import sqlite3, uuid
from database import connect, init_db, now

init_db()
conn = connect()

# 1. departments
for name in ["HR", "IT", "Finance"]:
    conn.execute("INSERT OR IGNORE INTO departments(name) VALUES (?)", (name,))
conn.commit()

# 2. register a document record (status starts as 'queued')
hr = conn.execute("SELECT id FROM departments WHERE name = ?", ("HR",)).fetchone()["id"]
doc_id = uuid.uuid4().hex
conn.execute(
    "INSERT INTO documents(id, display_name, file_type, stored_name, department_id, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?)",
    (doc_id, "HR Policy.pdf", "pdf", f"{doc_id}.pdf", hr, now()))
conn.commit()

# 3. move it through the statuses
for status in ["extracting", "embedding", "indexed"]:
    conn.execute("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))
    conn.commit()

# 4. read it back
for row in conn.execute(
        "SELECT d.display_name, d.status, dep.name AS department "
        "FROM documents d JOIN departments dep ON dep.id = d.department_id"):
    print(dict(row))

# 5. the database must refuse bad data
try:
    conn.execute("INSERT INTO users(username, password_hash, role) VALUES ('x', 'h', 'boss')")
except sqlite3.IntegrityError as e:
    print("Refused bad role:", e)

try:
    conn.execute("INSERT INTO documents(id, display_name, file_type, stored_name, department_id, created_at) "
                 "VALUES ('z','a','pdf','z.pdf', 999, 'now')")
except sqlite3.IntegrityError as e:
    print("Refused unknown department:", e)

# 6. SQL injection attempt is harmless with a ? placeholder
evil = "x' OR '1'='1"
print("Injection result:", conn.execute("SELECT * FROM users WHERE username = ?", (evil,)).fetchone())

conn.close()
