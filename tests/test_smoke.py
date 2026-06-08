"""M0 acceptance: the app serves a page and the disclaimer is present."""
import pytest


@pytest.mark.django_db
def test_home_page_serves(client):
    resp = client.get("/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_disclaimer_present(client):
    resp = client.get("/")
    body = resp.content.decode()
    assert "not investment advice" in body
    assert "synthetic projects" in body
