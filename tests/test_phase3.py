"""Phase 3 tests: auth/BEC analyzers, feedback loop, body limits, API-key gating."""
import sys
from pathlib import Path

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


def test_bec_financial_and_secrecy():
    out = analyze_bec("Please wire transfer $5000 today. Keep this confidential, do not tell anyone.")
    assert out["risk"] > 0
    assert len(out["reasons"]) >= 2


def test_bec_clean_email_no_risk():
    out = analyze_bec("Hi team, meeting notes attached. Best, John")
    assert out["risk"] == 0


def test_detector_includes_new_evidence_channels():
    from backend.app.services.phishing_detector import detect_phishing
    out = detect_phishing(
        "CEO request: wire transfer immediately, keep confidential",
        "ceo@company-support.xyz",
        reply_to="ceo@other.xyz",
    )
    assert out["policy_version"] == "phase3-evidence-v2"
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
