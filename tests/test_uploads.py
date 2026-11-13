from pathlib import Path

from conftest import collection
from helpers import DOCS, dept_id, upload, upload_ok


def test_exe_renamed_to_pdf_is_rejected(client, as_user, db):
    r = upload(client, as_user("admin1"), db, "HR", "evil.pdf", b"MZ\x90\x00 not a pdf at all")
    assert r.status_code == 400


def test_unsupported_extension_is_rejected(client, as_user, db):
    assert upload(client, as_user("admin1"), db, "HR", "run.exe", b"hello").status_code == 400


def test_empty_file_is_rejected(client, as_user, db):
    assert upload(client, as_user("admin1"), db, "HR", "empty.txt", b"").status_code == 400


def test_oversized_file_is_413(client, as_user, db):
    big = b"a" * (25 * 1024 * 1024 + 10)
    assert upload(client, as_user("admin1"), db, "HR", "big.txt", big).status_code == 413


def test_stored_file_gets_a_random_name(client, as_user, db):
    upload_ok(client, as_user("admin1"), db, "HR", "../../hack.txt", "Some harmless policy text here.")
    stored = [p.name for p in (Path("data") / "uploads").glob("*")]
    assert len(stored) == 1 and "hack" not in stored[0]


def test_indexing_finishes_and_chunks_are_stored(client, as_user, db):
    doc_id = upload_ok(client, as_user("admin1"), db, "HR", "a.txt", "Leave policy text. " * 20)
    row = db.execute("SELECT status, chunk_count FROM documents WHERE id=?", (doc_id,)).fetchone()
    assert row["status"] == "indexed" and row["chunk_count"] >= 1
    assert collection.count() == row["chunk_count"]


def test_delete_removes_row_file_and_chunks(client, as_user, db):
    admin = as_user("admin1")
    doc_id = upload_ok(client, admin, db, "HR", "a.txt", "Leave policy text. " * 20)
    assert client.delete(f"{DOCS}/{doc_id}", headers=admin).status_code in (200, 204)
    assert db.execute("SELECT 1 FROM documents WHERE id=?", (doc_id,)).fetchone() is None
    assert collection.count() == 0
    assert list((Path("data") / "uploads").glob("*")) == []


def test_empty_pdf_text_gives_failed_status_with_reason(client, as_user, db):
    # a valid-looking PDF header but no readable pages
    doc = upload(client, as_user("admin1"), db, "HR", "broken.pdf", b"%PDF-1.4\n%%EOF")
    assert doc.status_code == 202
    row = db.execute("SELECT status, error_message FROM documents").fetchone()
    assert row["status"] == "failed" and row["error_message"]
