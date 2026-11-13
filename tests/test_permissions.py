import fake_ollama
from helpers import DOCS, ask, upload, upload_ok

HR_TEXT = "Employees may work remotely three days per week. Remote days must be agreed with the manager."
IT_TEXT = "The VPN password must be reset every ninety days. Contact the IT desk for a VPN token."


def setup_docs(client, as_user, db):
    admin = as_user("admin1")
    hr = upload_ok(client, admin, db, "HR", "remote_policy.txt", HR_TEXT)
    it = upload_ok(client, admin, db, "IT", "vpn_notes.txt", IT_TEXT)
    return hr, it


def test_staff_list_shows_only_own_department(client, as_user, db):
    setup_docs(client, as_user, db)
    names = [d["display_name"] for d in client.get(DOCS, headers=as_user("hr_anu")).json()]
    assert names == ["remote_policy.txt"]


def test_admin_sees_everything(client, as_user, db):
    setup_docs(client, as_user, db)
    assert len(client.get(DOCS, headers=as_user("admin1")).json()) == 2


def test_user_without_departments_sees_nothing(client, as_user, db):
    setup_docs(client, as_user, db)
    assert client.get(DOCS, headers=as_user("nodept")).json() == []
    r = ask(client, as_user("nodept"), "How many days can I work remotely?").json()
    assert r["status"] == "no_evidence"


def test_direct_link_to_other_departments_document_is_404(client, as_user, db):
    hr_id, it_id = setup_docs(client, as_user, db)
    assert client.get(f"{DOCS}/{hr_id}", headers=as_user("it_ravi")).status_code == 404
    assert client.get(f"{DOCS}/{hr_id}", headers=as_user("hr_anu")).status_code == 200


def test_other_department_question_never_reaches_the_model(client, as_user, db):
    setup_docs(client, as_user, db)
    r = ask(client, as_user("it_ravi"), "How many days can employees work remotely per week?").json()
    assert r["status"] == "no_evidence"
    assert fake_ollama.calls == []        # the HR text was never even sent to the model


def test_staff_cannot_upload_or_delete(client, as_user, db):
    hr_id, _ = setup_docs(client, as_user, db)
    assert upload(client, as_user("hr_anu"), db, "HR", "x.txt", b"hello there").status_code == 403
    assert client.delete(f"{DOCS}/{hr_id}", headers=as_user("hr_anu")).status_code == 403


def test_staff_cannot_read_audit_log(client, as_user):
    from helpers import AUDIT
    assert client.get(AUDIT, headers=as_user("hr_anu")).status_code == 403
    assert client.get(AUDIT, headers=as_user("admin1")).status_code == 200
