import security
from conftest import PASSWORD
from helpers import LOGIN

CHANGE = "/api/auth/change-password"
NEW = "a-brand-new-passphrase"


def make_user(db, name, password=PASSWORD):
    """A fresh user for each test, so changing a password never affects other tests."""
    db.execute("INSERT INTO users (username, password_hash, role) VALUES (?,?,'staff')",
               (name, security.hash_password(password)))
    db.commit()


def sign_in(client, name, password=PASSWORD):
    r = client.post(LOGIN, json={"username": name, "password": password})
    return r, ({"Authorization": "Bearer " + r.json()["token"]} if r.status_code == 200 else None)


def change(client, headers, current=PASSWORD, new=NEW):
    return client.post(CHANGE, headers=headers, json={"current_password": current, "new_password": new})


def test_requires_login(client):
    assert client.post(CHANGE, json={"current_password": "x", "new_password": "y" * 12}).status_code == 401


def test_change_works_and_old_password_stops_working(client, db):
    make_user(db, "pw_a")
    _, headers = sign_in(client, "pw_a")
    assert change(client, headers).status_code == 200
    assert sign_in(client, "pw_a", NEW)[0].status_code == 200
    assert sign_in(client, "pw_a", PASSWORD)[0].status_code == 401


def test_other_sessions_are_signed_out_but_this_one_stays(client, db):
    make_user(db, "pw_b")
    _, this_device = sign_in(client, "pw_b")
    _, other_device = sign_in(client, "pw_b")
    assert change(client, this_device).status_code == 200
    assert client.get("/api/documents", headers=this_device).status_code == 200
    assert client.get("/api/documents", headers=other_device).status_code == 401


def test_wrong_current_password_is_refused_and_changes_nothing(client, db):
    make_user(db, "pw_c")
    _, headers = sign_in(client, "pw_c")
    r = change(client, headers, current="not-my-password")
    assert r.status_code == 400                      # 400, so the website does not log the person out
    assert sign_in(client, "pw_c")[0].status_code == 200


def test_weak_or_same_or_username_passwords_are_refused(client, db):
    make_user(db, "pw_d")
    _, headers = sign_in(client, "pw_d")
    assert change(client, headers, new="short").status_code == 400
    assert change(client, headers, new=PASSWORD).status_code == 400
    assert change(client, headers, new="pw_d").status_code == 400      # too short anyway
    make_user(db, "long_username_user")
    _, h2 = sign_in(client, "long_username_user")
    assert change(client, h2, new="LONG_username_USER").status_code == 400


def test_five_wrong_current_passwords_lock_the_account(client, db):
    make_user(db, "pw_e")
    _, headers = sign_in(client, "pw_e")
    for _ in range(5):
        change(client, headers, current="guess")
    assert sign_in(client, "pw_e")[0].status_code == 429
    assert client.get("/api/documents", headers=headers).status_code == 401   # the session ended too


def test_audit_records_the_change_but_never_the_password(client, db):
    make_user(db, "pw_f")
    _, headers = sign_in(client, "pw_f")
    change(client, headers)
    rows = db.execute("SELECT username, event, detail FROM audit_log WHERE event='password_changed'").fetchall()
    assert [r["username"] for r in rows] == ["pw_f"]
    dump = " ".join(str(tuple(r)) for r in db.execute("SELECT * FROM audit_log"))
    assert NEW not in dump and PASSWORD not in dump


def test_new_password_is_stored_hashed(client, db):
    make_user(db, "pw_g")
    _, headers = sign_in(client, "pw_g")
    change(client, headers)
    stored = db.execute("SELECT password_hash FROM users WHERE username='pw_g'").fetchone()[0]
    assert stored.startswith("$argon2") and NEW not in stored
