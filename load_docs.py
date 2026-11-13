"""Upload every file in docs\\<Department>\\ through the running backend, as admin1.
Run with the backend AND Ollama running:   python load_docs.py
"""
import getpass
import json
import os
import sys
import time
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8000"
DOCS = Path("docs")
if not DOCS.exists():
    sys.exit("No docs folder here. Run this from C:\\Users\\anusu\\privatedocs.")


def call(method, path, **kw):
    try:
        return httpx.request(method, BASE + path, trust_env=False, timeout=300, **kw)
    except httpx.ConnectError:
        sys.exit("The backend is not running. Start uvicorn first.")


r = call("POST", "/api/auth/login", json={"username": "admin1", "password": os.environ.get("PD_DEMO_PASSWORD") or getpass.getpass("Password for admin1: ")})
if r.status_code != 200:
    sys.exit(f"Login failed ({r.status_code}). Wrong password?")
headers = {"Authorization": "Bearer " + r.json()["token"]}

dept_ids = {d["name"]: d["id"] for d in call("GET", "/api/departments", headers=headers).json()}
dates_file = DOCS / "dates.json"      # {"file name": "YYYY-MM-DD"}: the day each document starts to apply
dates = json.loads(dates_file.read_text(encoding="utf-8")) if dates_file.exists() else {}
id_to_name = {v: k for k, v in dept_ids.items()}
existing = {d["display_name"] for d in call("GET", "/api/documents", headers=headers).json()}

for folder in sorted(p for p in DOCS.iterdir() if p.is_dir()):
    if folder.name not in dept_ids:
        print(f"Skipping folder {folder.name}: no such department")
        continue
    for file in sorted(folder.iterdir()):
        if file.name in existing:
            print(f"Already uploaded, skipped: {file.name}")
            continue
        with open(file, "rb") as f:
            r = call("POST", "/api/documents", headers=headers,
                     files={"file": (file.name, f)}, data={"department_id": str(dept_ids[folder.name]), **({"effective_date": dates[file.name]} if file.name in dates else {})})
        print(f"{folder.name:<8} {file.name:<32} upload status {r.status_code}")
        if r.status_code != 202:
            print("   ", r.text)

print("Waiting for indexing...")
for _ in range(90):
    docs = call("GET", "/api/documents", headers=headers).json()
    busy = [d for d in docs if d["status"] not in ("indexed", "failed")]
    if not busy:
        break
    time.sleep(2)
print(f"\n{'document':<34} {'department':<10} {'status':<9} chunks")
for d in docs:
    dept = d.get("department") or d.get("department_name") or id_to_name.get(d.get("department_id"), d.get("department_id"))
    chunks = d.get("chunk_count", d.get("chunks", "?"))
    print(f"{d['display_name']:<34} {str(dept):<10} {d['status']:<9} {chunks}")
bad = [d for d in docs if d["status"] != "indexed"]
print("\nAll documents indexed." if not bad else f"\n{len(bad)} document(s) not indexed. See the table.")
