import sqlite3

import pytest

import database
import security
from conftest import PASSWORD, login
from helpers import ASK, DOCS, LOGIN, LOGOUT

CHANGE = "/api/auth/change-password"
NEW_PASSWORD = "my-very-own-new-password"


@pytest.fixture
def newbie(db):
    """A staff user an admin has just created: must choose a new password."""
    h = security.hash_password(PASSWORD)
    db.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES ('newbie', ?, 'staff')", (h,))
    db.execute("UPDATE users SET password_hash = ?, must_change_password = 1, failed_attempts = 0, locked_until = NULL "
               "WHERE username = 'newbie'", (h,))
    db.commit()
    return "newbie"


def headers(client, username):
    r = login(client, username)
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}, r.json()


def test_login_tells_the_website_that_a_change_is_required(client, newbie):
    _, body = headers(client, newbie)
    assert body["must_change_password"] is True


def test_normal_users_are_not_forced(client):
    _, body = headers(client, "hr_anu")
    assert body["must_change_password"] is False


def test_everything_else_is_blocked_until_the_password_is_changed(client, newbie):
    h, _ = headers(client, newbie)
    for r in (client.get(DOCS, headers=h), client.post(ASK, headers=h, json={"question": "How many days?"}),
              client.get("/api/departments", headers=h)):
        assert r.status_code == 403
        assert r.json()["detail"] == "password_change_required"


def test_changing_the_password_unlocks_the_session(client, newbie, db):
    h, _ = headers(client, newbie)
    r = client.post(CHANGE, headers=h, json={"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert r.status_code == 200, r.text
    assert client.get("/api/departments", headers=h).status_code == 200      # same session, now allowed
    assert db.execute("SELECT must_change_password FROM users WHERE username='newbie'").fetchone()[0] == 0
    assert login(client, newbie, NEW_PASSWORD).json()["must_change_password"] is False


def test_a_bad_new_password_keeps_the_block(client, newbie):
    h, _ = headers(client, newbie)
    r = client.post(CHANGE, headers=h, json={"current_password": PASSWORD, "new_password": "short"})
    assert r.status_code == 400
    assert client.get("/api/departments", headers=h).status_code == 403


def test_signing_out_is_always_possible(client, newbie):
    h, _ = headers(client, newbie)
    assert client.post(LOGOUT, headers=h).status_code == 204


def test_old_databases_get_the_new_column(tmp_path, monkeypatch):
    old = tmp_path / "old.db"
    conn = sqlite3.connect(old)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, "
                 "role TEXT NOT NULL, failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until TEXT)")
    conn.execute("INSERT INTO users (username, password_hash, role) VALUES ('old_user', 'x', 'staff')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(database, "DB_PATH", old)
    database.init_db()
    database.init_db()                                   # twice is fine
    conn = sqlite3.connect(old)
    assert conn.execute("SELECT must_change_password FROM users WHERE username='old_user'").fetchone()[0] == 0
    conn.close()
