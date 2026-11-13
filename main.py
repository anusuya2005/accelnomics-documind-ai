import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from privacy import build_status

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from chunking import make_chunks
from database import connect, init_db, now
from ollama_client import CHAT_MODEL, ModelUnavailable, chat, embed
from permissions import allowed_department_ids
from readers import ExtractionError, read_document
from security import DUMMY_HASH, hash_password, hash_token, new_token, verify_password
from vector_store import collection
from answering import answer_question

UPLOADS = Path("data") / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
MAX_MB = 25
MIN_SIMILARITY = 0.35          # below this, a chunk is not relevant (tuned properly in Phase 8)
ALLOWED = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}

init_db()
_conn = connect()
for _name in ["HR", "IT", "Finance"]:
    _conn.execute("INSERT OR IGNORE INTO departments(name) VALUES (?)", (_name,))
_conn.commit()
_conn.close()

app = FastAPI(title="Accelnomics DocuMind AI")


@app.exception_handler(ModelUnavailable)
def model_unavailable(_, exc):
    return JSONResponse(status_code=503, content={"error": str(exc)})


# ---------------------------------------------------------------- login
bearer = HTTPBearer(auto_error=False)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


def log_event(conn, username, event, detail=None):
    """One line in the audit log. Never put a password, a token or a question in here."""
    conn.execute("INSERT INTO audit_log(ts, username, event, detail) VALUES (?, ?, ?, ?)", (now(), username, event, detail))


@app.post("/api/auth/login")
def login(body: LoginIn):
    conn = connect()
    try:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (body.username,)).fetchone()
        if user and user["locked_until"] and user["locked_until"] > now():
            log_event(conn, user["username"], "login_blocked")
            conn.commit()
            raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")

        # Always check against SOME hash, so an unknown user takes as long as a wrong password.
        ok = verify_password(user["password_hash"] if user else DUMMY_HASH, body.password) and user is not None
        if not ok:
            if user:
                attempts = user["failed_attempts"] + 1
                locked = None
                if attempts >= 5:
                    locked = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds")
                conn.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                             (0 if locked else attempts, locked, user["id"]))
                log_event(conn, user["username"], "login_failed")
                if locked:
                    log_event(conn, user["username"], "account_locked", "login")
            else:
                # The typed name is NOT stored: someone may have typed their password into the username box.
                log_event(conn, None, "login_unknown")
            conn.commit()
            raise HTTPException(401, "Invalid username or password.")     # same message in both cases

        token, token_hash = new_token()
        expires = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(timespec="seconds")
        conn.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
        conn.execute("INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                     (token_hash, user["id"], expires))
        conn.execute("INSERT INTO audit_log(ts, username, event) VALUES (?, ?, 'login')", (now(), user["username"]))
        conn.commit()
        return {"token": token, "role": user["role"], "username": user["username"],
                "must_change_password": bool(user["must_change_password"])}
    finally:
        conn.close()


# While a person must choose a new password, these are the ONLY things their session may do.
ALLOWED_WHILE_MUST_CHANGE = {"/api/auth/change-password", "/api/auth/logout"}


def current_user(request: Request, creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if creds is None:
        raise HTTPException(401, "Please sign in.")
    conn = connect()
    try:
        user = conn.execute(
            "SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (hash_token(creds.credentials), now())).fetchone()
    finally:
        conn.close()
    if user is None:
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    if user["must_change_password"] and request.url.path not in ALLOWED_WHILE_MUST_CHANGE:
        raise HTTPException(403, "password_change_required")
    return dict(user)


def admin_required(user: dict = Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(403, "This action needs an administrator.")
    return user


@app.post("/api/auth/logout", status_code=204)
def logout(creds: HTTPAuthorizationCredentials = Depends(bearer), user: dict = Depends(current_user)):
    conn = connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(creds.credentials),))
        conn.execute("INSERT INTO audit_log(ts, username, event) VALUES (?, ?, 'logout')", (now(), user["username"]))
        conn.commit()
    finally:
        conn.close()


class ChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)


MIN_PASSWORD = 10


@app.post("/api/auth/change-password")
def change_password(body: ChangePasswordIn, creds: HTTPAuthorizationCredentials = Depends(bearer),
                    user: dict = Depends(current_user)):
    """A signed-in person changes their OWN password. Nobody can change someone else's here."""
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
        if row["locked_until"] and row["locked_until"] > now():
            log_event(conn, row["username"], "password_change_blocked")
            conn.commit()
            raise HTTPException(429, "Too many failed attempts. Try again in 15 minutes.")

        if not verify_password(row["password_hash"], body.current_password):
            # A stolen session must not be able to guess the password forever: same lockout as the login.
            attempts = row["failed_attempts"] + 1
            locked = None
            if attempts >= 5:
                locked = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(timespec="seconds")
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user["id"],))
            conn.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
                         (0 if locked else attempts, locked, user["id"]))
            log_event(conn, row["username"], "password_change_failed")
            if locked:
                log_event(conn, row["username"], "account_locked", "change-password")
            conn.commit()
            raise HTTPException(400, "The current password is not correct.")   # 400, not 401: the session is fine

        if len(body.new_password) < MIN_PASSWORD:
            raise HTTPException(400, f"The new password must have at least {MIN_PASSWORD} characters.")
        if body.new_password == body.current_password:
            raise HTTPException(400, "The new password must be different from the current one.")
        if body.new_password.lower() == row["username"].lower():
            raise HTTPException(400, "The new password must not be your username.")

        conn.execute("UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL, "
                     "must_change_password = 0 WHERE id = ?",
                     (hash_password(body.new_password), user["id"]))
        # Every OTHER device or browser signed in as this person is signed out. This session stays.
        conn.execute("DELETE FROM sessions WHERE user_id = ? AND token_hash != ?",
                     (user["id"], hash_token(creds.credentials)))
        conn.execute("INSERT INTO audit_log(ts, username, event) VALUES (?, ?, 'password_changed')",
                     (now(), user["username"]))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# ---------------------------------------------------------------- helpers
def looks_like(file_type, head):
    """Check the real content, not just the file name."""
    if file_type == "pdf":
        return head.lstrip().startswith(b"%PDF-")
    if file_type == "docx":
        return head.startswith(b"PK")            # a .docx is a ZIP file
    return b"\x00" not in head                    # text files should have no NUL bytes


def marks(items):
    """'?,?,?' for an SQL IN (...) list."""
    return ",".join("?" * len(items))


# ---------------------------------------------------------------- indexing
def ingest(doc_id):
    """Runs in the background: read, chunk, embed, store. Status becomes 'indexed' LAST."""
    conn = connect()
    try:
        doc = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        try:
            conn.execute("UPDATE documents SET status='extracting' WHERE id=?", (doc_id,)); conn.commit()
            units = read_document(UPLOADS / doc["stored_name"])
            groups = [[u] for u in units] if doc["file_type"] == "pdf" else [units]
            chunks = [c for g in groups for c in make_chunks(g)]

            conn.execute("UPDATE documents SET status='embedding' WHERE id=?", (doc_id,)); conn.commit()
            vectors = []
            for i in range(0, len(chunks), 16):
                vectors += embed(["search_document: " + c["text"] for c in chunks[i:i + 16]])

            collection.upsert(
                ids=[f"{doc_id}:{i}" for i in range(len(chunks))],
                embeddings=vectors,
                documents=[c["text"] for c in chunks],
                metadatas=[{"doc_id": doc_id, "department_id": doc["department_id"],
                            "location": c["location"]} for c in chunks],
            )
            conn.execute("UPDATE documents SET status='indexed', chunk_count=?, error_message=NULL WHERE id=?",
                         (len(chunks), doc_id))
        except (ExtractionError, ModelUnavailable) as exc:
            conn.execute("UPDATE documents SET status='failed', error_message=? WHERE id=?", (str(exc), doc_id))
        except Exception:
            conn.execute("UPDATE documents SET status='failed', error_message='Unexpected error while indexing.' WHERE id=?",
                         (doc_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------- endpoints
@app.get("/api/login-options")
def login_options():
    """Public: only the names for the sign-in tiles. No users, no documents."""
    conn = connect()
    try:
        names = [r["name"] for r in conn.execute("SELECT name FROM departments ORDER BY id")]
        return {"options": ["Admin"] + names}
    finally:
        conn.close()

@app.get("/api/departments")
def departments(user: dict = Depends(current_user)):
    conn = connect()
    try:
        allowed = allowed_department_ids(conn, user)
        if not allowed:
            return []
        rows = conn.execute(f"SELECT id, name FROM departments WHERE id IN ({marks(allowed)}) ORDER BY id", allowed)
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.post("/api/documents", status_code=202)
def upload(background: BackgroundTasks, file: UploadFile = File(...), department_id: int = Form(...),
           effective_date: str | None = Form(None), user: dict = Depends(admin_required)):
    file_type = ALLOWED.get(Path(file.filename or "").suffix.lower())
    if file_type is None:
        raise HTTPException(400, "Only PDF, DOCX and TXT files are allowed.")

    effective_date = (effective_date or "").strip() or None
    if effective_date is not None:
        try:
            date.fromisoformat(effective_date)                    # must look like 2025-04-01
        except ValueError:
            raise HTTPException(400, "The date must look like 2025-04-01.")

    data = file.file.read(MAX_MB * 1024 * 1024 + 1)
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"The file is larger than {MAX_MB} MB.")
    if not data or not looks_like(file_type, data[:4096]):
        raise HTTPException(400, f"The file is empty or is not really a {file_type.upper()} file.")

    conn = connect()
    try:
        if conn.execute("SELECT 1 FROM departments WHERE id=?", (department_id,)).fetchone() is None:
            raise HTTPException(400, "Unknown department.")
        doc_id = uuid.uuid4().hex
        stored_name = f"{doc_id}.{file_type}"                 # random name: the user's name is never a path
        (UPLOADS / stored_name).write_bytes(data)
        conn.execute(
            "INSERT INTO documents(id, display_name, file_type, stored_name, department_id, created_at, effective_date) "
            "VALUES (?,?,?,?,?,?,?)",
            (doc_id, Path(file.filename).name[:200], file_type, stored_name, department_id, now(), effective_date))
        conn.execute("INSERT INTO audit_log(ts, username, event, detail) VALUES (?, ?, 'upload', ?)",
                     (now(), user["username"], doc_id))
        conn.commit()
    finally:
        conn.close()
    background.add_task(ingest, doc_id)                       # indexing happens after the reply is sent
    return {"id": doc_id, "status": "queued"}


@app.get("/api/documents")
def list_documents(user: dict = Depends(current_user)):
    conn = connect()
    try:
        allowed = allowed_department_ids(conn, user)          # read from the database, every time
        if not allowed:
            return []
        rows = conn.execute(
            "SELECT id, display_name, department_id, status, error_message, chunk_count, effective_date FROM documents "
            f"WHERE department_id IN ({marks(allowed)}) ORDER BY created_at DESC", allowed)
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str, user: dict = Depends(current_user)):
    conn = connect()
    try:
        allowed = allowed_department_ids(conn, user)
        doc = conn.execute(
            "SELECT id, display_name, department_id, status, error_message, chunk_count, effective_date "
            "FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if doc is None or doc["department_id"] not in allowed:
            raise HTTPException(404, "Document not found.")   # 404, not 403: do not reveal that it exists
        return dict(doc)
    finally:
        conn.close()


@app.delete("/api/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str, user: dict = Depends(admin_required)):
    conn = connect()
    try:
        doc = conn.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if doc is None:
            raise HTTPException(404, "Document not found.")
        conn.execute("UPDATE documents SET status='deleting' WHERE id=?", (doc_id,)); conn.commit()  # 1. hide
        collection.delete(where={"doc_id": doc_id})                                                  # 2. chunks
        (UPLOADS / doc["stored_name"]).unlink(missing_ok=True)                                       # 3. file
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))                                  # 4. row
        conn.execute("INSERT INTO audit_log(ts, username, event, detail) VALUES (?, ?, 'delete', ?)",
                     (now(), user["username"], doc_id))
        conn.commit()
    finally:
        conn.close()

class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@app.post("/api/ask")
def ask(body: AskIn, user: dict = Depends(current_user)):
    conn = connect()
    try:
        result = answer_question(conn, user, body.question.strip())
        # Extra facts for the "Why this answer?" panel. All of it comes from the database, not from the model.
        allowed = allowed_department_ids(conn, user)
        names = []
        if allowed:
            names = [r["name"] for r in conn.execute(
                f"SELECT name FROM departments WHERE id IN ({marks(allowed)}) ORDER BY id", allowed)]
        result["scope"] = {"departments": names, "model": CHAT_MODEL}
        for citation in result.get("citations", []):
            row = conn.execute("SELECT effective_date FROM documents WHERE id = ?",
                               (citation["document_id"],)).fetchone()
            citation["effective_date"] = row["effective_date"] if row else None
        return result
    finally:
        conn.close()
# ---------------------------------------------------------------- privacy console
@app.get("/api/privacy/status")
def privacy_status(user: dict = Depends(admin_required)):
    conn = connect()
    try:
        return build_status(conn, user)
    finally:
        conn.close()


@app.get("/api/admin/audit")
def audit(limit: int = 50, user: dict = Depends(admin_required)):
    limit = max(1, min(limit, 200))
    conn = connect()
    try:
        rows = conn.execute("SELECT ts, username, event, detail FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        events = [dict(r) for r in rows]
        counts = {r["event"]: r["n"] for r in conn.execute("SELECT event, COUNT(*) AS n FROM audit_log GROUP BY event")}
        return {"counts": counts, "recent": events}
    finally:
        conn.close()


# ---------------------------------------------------------------- the website (one port, no Node needed)
# Must stay the LAST thing in this file: it catches every path that is not an /api route.
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="website")