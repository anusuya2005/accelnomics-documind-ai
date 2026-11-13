import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# IMPORTANT: move into a throw-away folder BEFORE importing the app.
# The app uses relative paths (data/...), so tests must never touch the real data folder.
_TMP = tempfile.mkdtemp(prefix="privatedocs_test_")
os.chdir(_TMP)
for py in BACKEND.glob("*.py"):                 # the privacy page scans *.py in the current folder
    shutil.copy(py, _TMP)

import database, ollama_client, security, fake_ollama, helpers   # noqa: E402
ollama_client._post = fake_ollama.fake_post              # the pretend Ollama
import main                                              # noqa: E402
from vector_store import collection                      # noqa: E402
from fastapi.testclient import TestClient                # noqa: E402

PASSWORD = "correct-horse-battery"


def _seed():
    conn = database.connect()
    for name in ("HR", "IT", "Finance"):
        conn.execute("INSERT OR IGNORE INTO departments (name) VALUES (?)", (name,))
    h = security.hash_password(PASSWORD)
    users = {"admin1": ("admin", []), "hr_anu": ("staff", ["HR"]), "it_ravi": ("staff", ["IT"]),
             "nodept": ("staff", [])}
    for name, (role, deps) in users.items():
        conn.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?,?,?)", (name, h, role))
        uid = conn.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()["id"]
        for d in deps:
            did = conn.execute("SELECT id FROM departments WHERE name=?", (d,)).fetchone()["id"]
            conn.execute("INSERT OR IGNORE INTO user_departments VALUES (?,?)", (uid, did))
    conn.commit()
    conn.close()


_seed()


@pytest.fixture(autouse=True)
def clean_state():
    """Every test starts with: no documents, no sessions, no audit rows, nobody locked."""
    conn = database.connect()
    for table in ("sessions", "documents", "audit_log"):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL")
    conn.commit()
    conn.close()
    ids = collection.get()["ids"]
    if ids:
        collection.delete(ids=ids)
    for f in (Path("data") / "uploads").glob("*"):
        f.unlink()
    fake_ollama.calls.clear()
    fake_ollama.forced_reply[0] = None
    yield


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def db():
    conn = database.connect()
    yield conn
    conn.close()


def login(client, username, password=PASSWORD):
    r = client.post(helpers.LOGIN, json={"username": username, "password": password})
    return r


@pytest.fixture
def as_user(client):
    def _as(username):
        r = login(client, username)
        assert r.status_code == 200, r.text
        return {"Authorization": "Bearer " + r.json()["token"]}
    return _as
