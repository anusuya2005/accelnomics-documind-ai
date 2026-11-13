import sqlite3

import database
from conftest import PASSWORD
from helpers import DEPT_FIELD, DOCS, FILE_FIELD, ask, dept_id, upload_ok

POLICY = "Employees may work remotely three days per week. Remote days must be agreed with the manager."
Q = "How many days per week can employees work remotely?"


def upload_dated(client, headers, db, dept, name, text, when):
    import io
    return client.post(DOCS, headers=headers,
                       files={FILE_FIELD: (name, io.BytesIO(text.encode()), "text/plain")},
                       data={DEPT_FIELD: str(dept_id(db, dept)), "effective_date": when})


def test_answer_says_which_departments_were_searched(client, as_user, db):
    upload_ok(client, as_user("admin1"), db, "HR", "remote_policy.txt", POLICY)
    hr = ask(client, as_user("hr_anu"), Q).json()
    assert hr["scope"]["departments"] == ["HR"]
    assert hr["scope"]["model"]
    admin = ask(client, as_user("admin1"), Q).json()
    assert admin["scope"]["departments"] == ["HR", "IT", "Finance"]


def test_scope_is_present_even_when_nothing_is_found(client, as_user, db):
    r = ask(client, as_user("it_ravi"), Q).json()
    assert r["status"] == "no_evidence" and r["scope"]["departments"] == ["IT"]


def test_user_without_departments_searches_nothing(client, as_user):
    r = ask(client, as_user("nodept"), Q).json()
    assert r["scope"]["departments"] == []


def test_effective_date_is_stored_listed_and_shown_in_citation(client, as_user, db):
    r = upload_dated(client, as_user("admin1"), db, "HR", "remote_policy.txt", POLICY, "2025-04-01")
    assert r.status_code == 202
    listed = client.get(DOCS, headers=as_user("hr_anu")).json()
    assert listed[0]["effective_date"] == "2025-04-01"
    answer = ask(client, as_user("hr_anu"), Q).json()
    assert answer["citations"][0]["effective_date"] == "2025-04-01"


def test_document_without_date_still_works(client, as_user, db):
    upload_ok(client, as_user("admin1"), db, "HR", "remote_policy.txt", POLICY)
    assert client.get(DOCS, headers=as_user("hr_anu")).json()[0]["effective_date"] is None


def test_bad_date_is_rejected(client, as_user, db):
    for bad in ("tomorrow", "2025-13-45", "01/04/2025"):
        r = upload_dated(client, as_user("admin1"), db, "HR", "x.txt", POLICY, bad)
        assert r.status_code == 400, bad


def test_old_database_gets_the_new_column(tmp_path, monkeypatch):
    old = tmp_path / "old.db"
    c = sqlite3.connect(old)
    c.execute("CREATE TABLE documents (id TEXT PRIMARY KEY, display_name TEXT NOT NULL, file_type TEXT NOT NULL,"
              " stored_name TEXT NOT NULL, department_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'queued',"
              " error_message TEXT, chunk_count INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)")
    c.commit(); c.close()
    monkeypatch.setattr(database, "DB_PATH", old)
    database.init_db()
    cols = [r[1] for r in sqlite3.connect(old).execute("PRAGMA table_info(documents)")]
    assert "effective_date" in cols
    database.init_db()          # running it twice must not fail
