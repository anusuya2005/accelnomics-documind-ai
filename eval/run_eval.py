"""Run:  python eval\run_eval.py [questions_file]
Example: python eval\run_eval.py questions_bank.json
Asks for each test user's password once, asks every question, prints PASS/FAIL."""
import getpass, json, sys
from pathlib import Path
import httpx

BASE = "http://127.0.0.1:8000"
qfile = sys.argv[1] if len(sys.argv) > 1 else "questions.json"
questions = json.loads((Path(__file__).parent / qfile).read_text(encoding="utf-8"))
tokens = {}
passwords = {}
passed = 0


def token_for(user):
    if user not in tokens:
        if not passwords:      # first user: ask once; the demo users share one password
            passwords["all"] = getpass.getpass("Password for the demo users (same for all): ")
        r = httpx.post(f"{BASE}/api/auth/login", json={"username": user, "password": passwords["all"]},
                       trust_env=False)
        if r.status_code != 200:
            sys.exit(f"Login failed for {user} (status {r.status_code}). Wrong password? "
                     "Careful: 5 wrong tries lock the account for 15 minutes.")
        tokens[user] = r.json()["token"]
    return tokens[user]


print(f"{'id':>3} {'kind':<17} {'result':<6} detail")
for item in questions:
    r = httpx.post(f"{BASE}/api/ask", json={"question": item["q"]}, trust_env=False, timeout=300,
                   headers={"Authorization": "Bearer " + token_for(item["user"])})
    body = r.json()
    ok, why = True, body.get("status", "?")
    if "expect_status" in item and body.get("status") != item["expect_status"]:
        ok, why = False, f"got {body.get('status')}, wanted {item['expect_status']}"
    if "expect_doc" in item:
        docs = [c["document"] for c in body.get("citations", [])]
        if item["expect_doc"] not in docs:
            ok, why = False, f"cited {docs}, wanted {item['expect_doc']}"
        text = body.get("answer", "").lower()
        if not all(w.lower() in text for w in item["expect_words"]):
            ok, why = False, f"answer lacks {item['expect_words']}"
    passed += ok
    print(f"{item['id']:>3} {item['kind']:<17} {'PASS' if ok else 'FAIL':<6} {why}")
print(f"\n{passed}/{len(questions)} passed")
sys.exit(0 if passed == len(questions) else 1)