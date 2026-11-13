import httpx

from helpers import PRIVACY


def test_privacy_status_requires_login(client):
    assert client.get(PRIVACY).status_code == 401


def test_privacy_status_all_checks_pass(client, as_user, monkeypatch):
    class R:
        def raise_for_status(self): pass
        def json(self):
            import ollama_client
            return {"models": [{"name": ollama_client.CHAT_MODEL}, {"name": ollama_client.EMBED_MODEL + ":latest"}]}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: R())
    body = client.get(PRIVACY, headers=as_user("admin1")).json()
    failed = [c["id"] for c in body["checks"] if c["status"] != "pass"]
    assert body["checks"] and failed == [], failed


def test_privacy_status_is_admin_only(client, as_user):
    assert client.get(PRIVACY, headers=as_user("hr_anu")).status_code == 403
