"""Start the demo from a clean slate.
Run with the backend STOPPED:   python reset_demo.py
1. Asks for the demo password (or reads PD_DEMO_PASSWORD when reset_and_start.ps1 runs it).
2. Moves the old data folder to data_backup_<date> (nothing is deleted).
3. Creates a fresh database with departments and users.
Then start the backend and run:  python load_docs.py
"""
import getpass
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

DATA = Path("data")
DEPARTMENTS = ["HR", "IT", "Finance"]
USERS = [                      # (username, role, departments)
    ("admin1", "admin", []),
    ("hr_anu", "staff", ["HR"]),
    ("it_ravi", "staff", ["IT"]),
    ("fin_meena", "staff", ["Finance"]),
]

# Check the password FIRST, so a typing mistake never touches your data.
password = os.environ.get("PD_DEMO_PASSWORD")
if not password:
    password = getpass.getpass("Choose ONE password for all demo users (min 10 characters): ")
    if password != getpass.getpass("Type it again: "):
        sys.exit("The two passwords did not match. Nothing was changed.")
if len(password) < 10:
    sys.exit("Password too short (minimum 10 characters). Nothing was changed.")

if DATA.exists():
    backup = Path(f"data_backup_{datetime.now():%Y%m%d_%H%M%S}")
    try:
        shutil.move(str(DATA), str(backup))
    except PermissionError:
        sys.exit("Cannot move the data folder. Stop the backend (uvicorn) and try again.")
    print(f"Old data kept in {backup}")

import database, security          # imported after the move, so the new database is created fresh

database.init_db()
conn = database.connect()
for name in DEPARTMENTS:
    conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
password_hash = security.hash_password(password)
for username, role, departments in USERS:
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
                 (username, password_hash, role))
    uid = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
    for dept in departments:
        did = conn.execute("SELECT id FROM departments WHERE name = ?", (dept,)).fetchone()["id"]
        conn.execute("INSERT INTO user_departments (user_id, department_id) VALUES (?,?)", (uid, did))
conn.commit()
conn.close()
print("Created departments:", ", ".join(DEPARTMENTS))
print("Created users:", ", ".join(u[0] for u in USERS))
print("Next: start the backend, then run  python load_docs.py")
