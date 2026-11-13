import re
from pathlib import Path

from ollama_client import CHAT_MODEL, EMBED_MODEL, OLLAMA, ModelUnavailable, installed_models
from permissions import allowed_department_ids
from vector_store import TELEMETRY

LOCAL_HOSTS = ("127.0.0.1", "localhost")
_URL = re.compile(r"https?://([^/\s:'\"]+)")
_CLOUD_IMPORT = re.compile(r"^\s*(?:import|from)\s+(openai|anthropic|google|boto3|cohere|azure)\b", re.M)


def _project_files():
    return sorted(Path(".").glob("*.py"))


def scan_for_external_urls():
    """Every web address in the project's code that is not this computer."""
    findings = []
    for path in _project_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for number, line in enumerate(text.splitlines(), start=1):
            for host in _URL.findall(line):
                if host not in LOCAL_HOSTS:
                    findings.append(f"{path.name}:{number} -> {host}")
    return findings


def scan_for_cloud_libraries():
    findings = []
    for path in _project_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in _CLOUD_IMPORT.finditer(text):
            findings.append(f"{path.name}: imports {match.group(1)}")
    return findings


def _check(check_id, title, ok, detail):
    return {"id": check_id, "title": title, "status": "pass" if ok else "fail", "detail": detail}


def build_status(conn, user):
    is_admin = user["role"] == "admin"
    checks = []

    host = re.match(r"https?://([^/:]+)", OLLAMA).group(1)
    checks.append(_check("ollama_local", "The AI model runs on this computer", host in LOCAL_HOSTS,
                         f"Ollama is reached at {OLLAMA}."))

    try:
        names = installed_models()
        missing = [m for m in (CHAT_MODEL, EMBED_MODEL)
                   if not any(n == m or n.startswith(m + ":") for n in names)]
        checks.append(_check("models_installed", "Both models are installed locally", not missing,
                             "Installed." if not missing else "Missing: " + ", ".join(missing)))
    except ModelUnavailable:
        names = []
        checks.append(_check("models_installed", "Both models are installed locally", False,
                             "Ollama is not reachable. Start Ollama."))

    checks.append(_check("telemetry_off", "Search index sends no usage reports", not TELEMETRY,
                         "ChromaDB anonymous telemetry is switched off in the code."))

    urls = scan_for_external_urls()
    checks.append(_check("no_external_urls", "No outside web addresses in the application code", not urls,
                         "Scanned the project's Python files." if not urls else "; ".join(urls[:10])))

    libs = scan_for_cloud_libraries()
    checks.append(_check("no_cloud_libraries", "No cloud AI libraries are used", not libs,
                         "Scanned the imports." if not libs else "; ".join(libs[:10])))

    # Counts come from SQLite and cover only the departments this user may see.
    allowed = allowed_department_ids(conn, user)
    by_status, chunks = {}, 0
    if allowed:
        marks = ",".join("?" * len(allowed))
        rows = conn.execute(f"SELECT status, COUNT(*) AS n, SUM(chunk_count) AS c FROM documents "
                            f"WHERE department_id IN ({marks}) GROUP BY status", allowed)
        for r in rows:
            by_status[r["status"]] = r["n"]
            if r["status"] == "indexed":
                chunks = r["c"] or 0

    storage = {"documents_by_status": by_status, "indexed_chunks": chunks}
    if is_admin:
        data_dir = Path("data")
        size = sum(f.stat().st_size for f in (data_dir / "uploads").glob("*") if f.is_file()) \
            if (data_dir / "uploads").exists() else 0
        storage["data_folder"] = str(data_dir.resolve())
        storage["uploads_size_mb"] = round(size / 1024 / 1024, 2)

    return {
        "checks": checks,
        "models": {"chat": CHAT_MODEL, "embedding": EMBED_MODEL, "installed": names if is_admin else []},
        "storage": storage,
        "what_stays_local": [
            "Uploaded files, extracted text and search vectors are stored in the data folder on this computer.",
            "Questions and answers are processed by the local model. Nothing is sent to an outside service.",
        ],
        "what_is_logged": [
            "Sign-ins, uploads, deletions and suspicious text events, with the username and a document id.",
            "Document text and questions are never written to the audit log.",
        ],
        "limits": [
            "These checks are run by the application on itself. They do not replace an independent review "
            "or the network-unplugged test.",
        ],
    }
