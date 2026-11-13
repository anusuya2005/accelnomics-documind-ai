"""Admin tool for a forgotten password. Run on the PC that holds the data, with the backend stopped or running:
    python set_password.py hr_anu
Add --keep to let the person keep this password (otherwise they must choose their own at next login).
Asks for the new password (minimum 10 characters) and signs the person out everywhere.
"""
import getpass
import sys

import database
import security

args = [a for a in sys.argv[1:] if a != "--keep"]
keep = "--keep" in sys.argv[1:]
if len(args) != 1:
    sys.exit("Usage: python set_password.py USERNAME [--keep]")
username = args[0]
database.init_db()

conn = database.connect()
user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
if user is None:
    sys.exit(f"There is no user called {username}.")

password = getpass.getpass(f"New password for {username} (min 10 characters): ")
if len(password) < 10:
    sys.exit("Too short. Nothing was changed.")
if password != getpass.getpass("Type it again: "):
    sys.exit("The two passwords did not match. Nothing was changed.")

conn.execute("UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL, "
             "must_change_password = ? WHERE id = ?",
             (security.hash_password(password), 0 if keep else 1, user["id"]))
conn.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
conn.execute("INSERT INTO audit_log (ts, username, event, detail) VALUES (?, ?, 'password_reset_by_admin', ?)",
             (database.now(), username, "offline tool"))
conn.commit()
conn.close()
print(f"Password changed for {username}. They are signed out everywhere."
      + ("" if keep else " They must choose a new password at next login."))
