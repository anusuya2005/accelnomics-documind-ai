import getpass, json, sys
import httpx

BASE = "http://127.0.0.1:8000"
user, question = sys.argv[1], sys.argv[2]
password = getpass.getpass(f"Password for {user}: ")
r = httpx.post(f"{BASE}/api/auth/login", json={"username": user, "password": password}, trust_env=False)
r.raise_for_status()
h = {"Authorization": "Bearer " + r.json()["token"]}
a = httpx.post(f"{BASE}/api/ask", json={"question": question}, headers=h, timeout=300, trust_env=False).json()
print(json.dumps(a, indent=2, ensure_ascii=False))