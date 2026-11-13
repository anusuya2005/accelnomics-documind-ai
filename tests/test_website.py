from pathlib import Path

import pytest

import main

pytestmark = pytest.mark.skipif(not main.FRONTEND_DIST.is_dir(), reason="run npm run build in frontend first")


def test_website_is_served_from_the_backend_port(client):
    r = client.get("/")
    assert r.status_code == 200 and "<div id=\"root\">" in r.text


def test_api_routes_still_win_over_the_website(client):
    r = client.get("/api/login-options")
    assert r.status_code == 200 and r.json()["options"][0] == "Admin"


def test_protected_api_still_needs_login(client):
    assert client.get("/api/documents").status_code == 401


def test_app_can_be_installed_manifest_and_icons_are_served(client):
    m = client.get("/manifest.webmanifest")
    assert m.status_code == 200
    data = m.json()
    assert data["name"] == "Accelnomics DocuMind AI" and data["display"] == "standalone"
    for icon in data["icons"]:
        assert client.get(icon["src"]).status_code == 200
