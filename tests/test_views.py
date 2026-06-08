"""M7 — view smoke tests. UI is demonstrated by the recording; here we just
confirm the pages serve and the budget/lambda controls re-optimize."""
import pytest

from engine.data.projects import TRAP_NAME
from engine.memo.schemas import InvestmentMemo
from web import services

pytestmark = pytest.mark.django_db


def test_pages_serve(client):
    for name in ("/", "/projects/", "/risk/", "/portfolio/"):
        assert client.get(name).status_code == 200


def test_portfolio_page_shows_funded_and_cut(client):
    body = client.get("/portfolio/").content.decode()
    assert "Funded" in body
    assert "Cut" in body


def test_optimize_partial_high_lambda_cuts_trap(client):
    resp = client.get("/portfolio/optimize/", {"budget": "1200", "lam": "1.0"})
    assert resp.status_code == 200
    body = resp.content.decode()
    # At high lambda the cut-callout names the trap as the high-NPV project cut.
    assert f"</strong> {TRAP_NAME} (" in body


def test_optimize_partial_low_lambda_funds_trap(client):
    resp = client.get("/portfolio/optimize/", {"budget": "1200", "lam": "0.0"})
    body = resp.content.decode()
    assert TRAP_NAME in body  # still present — now in the funded table
    # At lambda=0 the trap is funded, so it is NOT the project named in the cut callout.
    assert f"</strong> {TRAP_NAME} (" not in body


def test_optimize_handles_bad_params_gracefully(client):
    resp = client.get("/portfolio/optimize/", {"budget": "abc", "lam": ""})
    assert resp.status_code == 200


def test_memo_without_api_key_shows_notice(client, settings):
    settings.ANTHROPIC_API_KEY = ""
    resp = client.post("/portfolio/memo/", {"budget": "1200", "lam": "1.0"})
    assert resp.status_code == 200
    assert "ANTHROPIC_API_KEY" in resp.content.decode()


def test_memo_with_key_renders_generated_memo(client, settings, monkeypatch):
    settings.ANTHROPIC_API_KEY = "test-key"
    monkeypatch.setattr(
        services,
        "portfolio_memo",
        lambda *a, **k: InvestmentMemo(
            summary="SUMMARY-OK",
            funded_rationale="f",
            cut_rationale="c",
            risk_note="r",
        ),
    )
    resp = client.post("/portfolio/memo/", {"budget": "1200", "lam": "1.0"})
    assert resp.status_code == 200
    assert "SUMMARY-OK" in resp.content.decode()


def test_memo_requires_post(client):
    assert client.get("/portfolio/memo/").status_code == 405
