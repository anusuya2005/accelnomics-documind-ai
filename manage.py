import argparse
import getpass
import sqlite3

from database import connect, init_db
from security import hash_password


def prompt_password():
    while True:
        first = getpass.getpass("Password (at least 10 characters): ")
        if len(first) < 10:
            print("Too short.")
            continue
        if first != getpass.getpass("Repeat password: "):
            print("The two passwords do not match.")
            continue
        return first


def add_user(args):
    init_db()
    password = prompt_password()
    conn = connect()
    try:
        for name in ["HR", "IT", "Finance"]:
            conn.execute("INSERT OR IGNORE INTO departments(name) VALUES (?)", (name,))
        conn.execute("INSERT INTO users(username, password_hash, role) VALUES (?, ?, ?)",
                     (args.username, hash_password(password), args.role))
        user_id = conn.execute("SELECT id FROM users WHERE username = ?", (args.username,)).fetchone()["id"]
        for name in args.departments:
            dep = conn.execute("SELECT id FROM departments WHERE name = ?", (name,)).fetchone()
            if dep is None:
                raise SystemExit(f"Unknown department: {name}")
            conn.execute("INSERT INTO user_departments(user_id, department_id) VALUES (?, ?)", (user_id, dep["id"]))
        conn.commit()
        print(f"Created {args.role} '{args.username}'.")
    except sqlite3.IntegrityError:
        raise SystemExit(f"The username '{args.username}' already exists.")
    finally:
        conn.close()


parser = argparse.ArgumentParser()
sub = parser.add_subparsers(dest="cmd", required=True)
add = sub.add_parser("add-user")
add.add_argument("username")
add.add_argument("--role", choices=["admin", "staff"], default="staff")
add.add_argument("--departments", nargs="*", default=[])
add.set_defaults(func=add_user)

args = parser.parse_args()
args.func(args)
