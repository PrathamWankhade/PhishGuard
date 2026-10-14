"""Phase 3 tests: auth/BEC analyzers, feedback loop, body limits, API-key gating."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.services.auth_analyzer import analyze_auth
from backend.app.services.bec_analyzer import analyze_bec


def test_reply_to_mismatch_flagged():
    out = analyze_auth("ceo@company.com", reply_to="ceo@company-support.xyz")
    assert out["risk"] > 0
    assert any("Reply-To" in r for r in out["reasons"])


def test_matching_domains_no_risk():
    out = analyze_auth("a@company.com", reply_to="b@company.com", return_path="x@company.com")
    assert out["risk"] == 0


def test_spf_fail_flagged_spf_pass_noted():
    out = analyze_auth("a@x.com", auth_results="spf=fail dkim=pass")
    assert any("spf=fail" in r for r in out["reasons"])
    assert any("dkim=pass" in r for r in out["reasons"])


def test_forged_pass_claim_adds_no_risk():
    # Caller-supplied spf=pass proves nothing: informational only, zero risk.
    out = analyze_auth("evil@x.com", auth_results="spf=pass dkim=pass dmarc=pass")
    assert out["risk"] == 0
    assert all("unverified" in r for r in out["reasons"])


def test_trusted_fail_carries_full_weight():
    untrusted = analyze_auth("a@x.com", auth_results="spf=fail")
    trusted = analyze_auth("a@x.com", auth_results="spf=fail", trusted=True)
    assert trusted["risk"] > untrusted["risk"]
    assert any("Unverified" in r for r in untrusted["reasons"])
    assert all("Unverified" not in r for r in trusted["reasons"])


def test_bec_financial_and_secrecy():
    out = analyze_bec("Please wire transfer $5000 today. Keep this confidential, do not tell anyone.")
    assert out["risk"] > 0
    assert len(out["reasons"]) >= 2


def test_bec_clean_email_no_risk():
    out = analyze_bec("Hi team, meeting notes attached. Best, John")
    assert out["risk"] == 0


@pytest.mark.model
def test_detector_includes_new_evidence_channels():
    from backend.app.services.phishing_detector import detect_phishing
    out = detect_phishing(
        "CEO request: wire transfer immediately, keep confidential",
        "ceo@company-support.xyz",
        reply_to="ceo@other.xyz",
    )
    assert out["policy_version"] == "phase4-probability-v3"
    assert any("Reply-To" in s for s in out["signals"])
    assert any("Financial" in s or "fraud" in s for s in out["signals"])


def test_feedback_roundtrip():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    r = client.post("/api/v1/feedback", json={"email_hash": "abc123", "verdict_correct": False})
    assert r.status_code == 200
    r = client.get("/api/v1/feedback/stats")
    assert r.status_code == 200
    assert r.json()["total_reviews"] >= 1


def test_predict_rejects_oversized_body():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    big = "x" * 250_000
    r = client.post("/api/v1/predict", json={"email_text": big, "sender": "a@b.com"})
    assert r.status_code == 413


def test_cors_preflight_allows_api_key_header():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    r = client.options(
        "/api/v1/history",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Api-Key",
        },
    )
    assert r.status_code == 200
    assert "x-api-key" in r.headers.get("access-control-allow-headers", "").lower()


def test_history_gated_when_api_keys_configured(monkeypatch):
    import os
    from fastapi.testclient import TestClient

    monkeypatch.setenv("API_KEYS", "secret-1")
    # Re-read env at request time (middleware reads os.environ per request).
    assert os.environ["API_KEYS"] == "secret-1"
    from backend.app.main import app

    client = TestClient(app)
    assert client.get("/api/v1/history").status_code == 401
    assert client.get("/api/v1/history", headers={"X-API-Key": "wrong"}).status_code == 403


def test_expensive_routes_have_stricter_quota():
    from backend.app import main as app_main

    ip = "10.9.9.9"
    allowed = sum(1 for _ in range(35) if app_main.check_rate_limit(ip, "/api/v1/predict", now=1000.0))
    assert allowed == 30
    # Cheap routes keep the general 60/min budget on a fresh key.
    assert sum(1 for _ in range(61) if app_main.check_rate_limit("10.9.9.10", "/api/v1/history", now=1000.0)) == 60


def test_ai_budget_exhausted_stays_local(monkeypatch):
    import backend.app.services.openrouter_explainer as mod

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("AI_DAILY_BUDGET", "0")
    assert mod.generate_ai_explanation("hi", "a@b.com", "Safe Email", 10) is None


def test_ai_saturated_semaphore_stays_local(monkeypatch):
    import backend.app.services.openrouter_explainer as mod

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("AI_DAILY_BUDGET", "500")
    sem = mod._get_semaphore()
    for _ in range(8):
        sem.acquire(blocking=False)
    try:
        assert mod.generate_ai_explanation("hi", "a@b.com", "Safe Email", 10) is None
    finally:
        for _ in range(8):
            try:
                sem.release()
            except ValueError:
                pass


def test_saturated_provider_consumes_no_budget(monkeypatch):
    import backend.app.services.openrouter_explainer as mod

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    monkeypatch.setenv("AI_DAILY_BUDGET", "500")
    sem = mod._get_semaphore()
    for _ in range(8):
        sem.acquire(blocking=False)
    before = mod._ai_used_today
    try:
        mod.generate_ai_explanation("hi", "a@b.com", "Safe Email", 10)
    finally:
        for _ in range(8):
            try:
                sem.release()
            except ValueError:
                pass
    assert mod._ai_used_today == before


def test_invalid_ai_config_raises(monkeypatch):
    import pytest as _pytest
    import backend.app.services.openrouter_explainer as mod

    monkeypatch.setenv("AI_DAILY_BUDGET", "lots")
    with _pytest.raises(RuntimeError):
        mod._budget_allows()
    monkeypatch.setenv("AI_MAX_CONCURRENT", "0")
    with _pytest.raises(RuntimeError):
        mod._semaphore_size()


def test_explainer_import_safe_without_credentials(monkeypatch):
    """Regression: importing the explainer in CI (no keys) must not raise."""
    import importlib

    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("AI_EXPLANATIONS_ENABLED", "true")
    import backend.app.services.openrouter_explainer as mod

    importlib.reload(mod)  # must not raise OpenAIError
    assert mod.generate_ai_explanation("hi", "a@b.com", "Safe Email", 10) is None
