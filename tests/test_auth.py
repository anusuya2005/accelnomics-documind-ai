from datetime import datetime, timedelta, timezone

from conftest import login, PASSWORD
from helpers import DOCS, LOGOUT


def test_no_token_is_rejected(client):
    assert client.get(DOCS).status_code == 401


def test_good_login_gives_token_and_role(client):
    r = login(client, "hr_anu")
    assert r.status_code == 200
    assert r.json()["role"] == "staff" and r.json()["token"]


def test_unknown_user_and_wrong_password_look_identical(client):
    a = login(client, "hr_anu", "wrong-password")
    b = login(client, "nobody-here", "wrong-password")
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_five_failures_lock_the_account_even_for_the_right_password(client):
    for _ in range(5):
        login(client, "it_ravi", "wrong")
    assert login(client, "it_ravi", PASSWORD).status_code == 429


def test_expired_session_is_rejected(client, as_user, db):
    headers = as_user("hr_anu")
    old = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds")
    db.execute("UPDATE sessions SET expires_at = ?", (old,))
    db.commit()
    assert client.get(DOCS, headers=headers).status_code == 401


def test_logout_kills_the_token(client, as_user):
    headers = as_user("hr_anu")
    assert client.post(LOGOUT, headers=headers).status_code in (200, 204)
    assert client.get(DOCS, headers=headers).status_code == 401


def test_session_token_is_stored_hashed(client, as_user, db):
    headers = as_user("hr_anu")
    token = headers["Authorization"].split()[1]
    stored = [r["token_hash"] for r in db.execute("SELECT token_hash FROM sessions")]
    assert token not in stored


def test_password_is_stored_hashed(db):
    row = db.execute("SELECT password_hash FROM users WHERE username='hr_anu'").fetchone()
    assert PASSWORD not in row["password_hash"] and row["password_hash"].startswith("$argon2")
