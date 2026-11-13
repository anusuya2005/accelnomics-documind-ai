import conftest
from conftest import login
from helpers import LOGIN


def events(db):
    return [(r["username"], r["event"], r["detail"]) for r in db.execute("SELECT username, event, detail FROM audit_log ORDER BY id")]


def test_wrong_password_is_logged_for_a_known_user(client, db):
    assert login(client, "hr_anu", "wrong-password-1").status_code == 401
    assert ("hr_anu", "login_failed", None) in events(db)
    assert "wrong-password-1" not in str(events(db))


def test_unknown_user_is_logged_without_the_typed_name(client, db):
    r = client.post(LOGIN, json={"username": "my-secret-password-typed-here", "password": "x"})
    assert r.status_code == 401
    ev = events(db)
    assert (None, "login_unknown", None) in ev
    assert "my-secret-password-typed-here" not in str(ev)


def test_five_failures_lock_the_account_and_are_logged(client, db):
    for _ in range(5):
        assert login(client, "it_ravi", "wrong-password-1").status_code == 401
    ev = events(db)
    assert ev.count(("it_ravi", "login_failed", None)) == 5
    assert ("it_ravi", "account_locked", "login") in ev
    assert login(client, "it_ravi", "wrong-password-1").status_code == 429
    assert ("it_ravi", "login_blocked", None) in events(db)


def test_successful_login_is_still_logged(client, db):
    assert login(client, "hr_anu").status_code == 200
    assert ("hr_anu", "login", None) in events(db)


def test_wrong_current_password_on_change_is_logged(client, db, as_user):
    h = as_user("hr_anu")
    r = client.post("/api/auth/change-password", headers=h,
                    json={"current_password": "not-my-password-1", "new_password": "a-brand-new-password"})
    assert r.status_code == 400
    ev = events(db)
    assert ("hr_anu", "password_change_failed", None) in ev
    assert "not-my-password-1" not in str(ev) and "a-brand-new-password" not in str(ev)
