"""Create a user, or reset an existing one. For the person who runs the server.
Inside Docker:   docker compose exec app python create_user.py anu --role staff --dept HR
Without Docker:  python create_user.py anu --role staff --dept HR
Admins need no department. A person can have several:  --dept HR --dept IT
The person must choose their own password at first login. Add --keep-password to skip that (demo accounts only).
"""
import argparse
import getpass
import os
import sys

import database
import security

parser = argparse.ArgumentParser()
parser.add_argument("username")
parser.add_argument("--role", choices=["admin", "staff"], default="staff")
parser.add_argument("--dept", action="append", default=[], help="department name; repeat for several")
parser.add_argument("--keep-password", action="store_true", help="do NOT force a password change at first login")
args = parser.parse_args()

username = args.username.strip()
if not username or len(username) > 64:
    sys.exit("The username must be 1 to 64 characters.")

password = os.environ.get("DOCUMIND_PASSWORD")        # for scripts; otherwise it is asked and not shown
if not password:
    password = getpass.getpass(f"Password for {username} (min 10 characters): ")
    if password != getpass.getpass("Type it again: "):
        sys.exit("The two passwords did not match. Nothing was changed.")
if len(password) < 10 or password == username:
    sys.exit("The password needs at least 10 characters and must not be the username. Nothing was changed.")

database.init_db()
conn = database.connect()
must_change = 0 if args.keep_password else 1
conn.execute("INSERT INTO users (username, password_hash, role, must_change_password) VALUES (?, ?, ?, ?) "
             "ON CONFLICT(username) DO UPDATE SET password_hash = excluded.password_hash, role = excluded.role, "
             "failed_attempts = 0, locked_until = NULL, must_change_password = excluded.must_change_password",
             (username, security.hash_password(password), args.role, must_change))
user_id = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]
conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
conn.execute("DELETE FROM user_departments WHERE user_id = ?", (user_id,))
for name in args.dept:
    conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    dept_id = conn.execute("SELECT id FROM departments WHERE name = ?", (name,)).fetchone()["id"]
    conn.execute("INSERT OR IGNORE INTO user_departments (user_id, department_id) VALUES (?, ?)", (user_id, dept_id))
conn.execute("INSERT INTO audit_log (ts, username, event, detail) VALUES (?, ?, 'user_saved_by_admin', ?)",
             (database.now(), username, args.role))
conn.commit()
conn.close()
print(f"Saved {username} ({args.role}) in: {', '.join(args.dept) or 'no department'}."
      + ("" if args.keep_password else " They must choose a new password at first login."))
