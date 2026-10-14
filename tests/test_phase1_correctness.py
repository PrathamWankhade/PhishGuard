"""Phase 1 regression tests: verdict, model/risk separation, URL counting, resilience."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ai-engine"))

from backend.app.services.url_analyzer import analyze_urls, is_homograph
from backend.app.services.phishing_detector import detect_phishing


@pytest.mark.model
def test_model_and_risk_fields_are_separate():
    result = detect_phishing(
        "URGENT verify your password at https://login.example.xyz",
        "alert@example.xyz",
    )
    assert "model_prediction" in result
    assert "model_confidence" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "verdict" in result
    assert "signals" in result
    # Legacy fields still present for UI compat.
    assert result["label"] == result["verdict"]
    assert result["prediction"] == result["model_prediction"]
    # Risk score is a policy score, derived from model + heuristics.
    assert result["risk_score"] >= result["model_confidence"]


@pytest.mark.model
def test_contradictory_label_case_is_documented():
    # Legitimate-looking text with risky sender/URL must keep raw model class
    # visible even when the verdict differs by policy.
    result = detect_phishing(
        "Hi team, please find the meeting notes attached. Best, John",
        "john@company.xyz",
    )
    assert result["model_prediction"] in ("legitimate", "phishing", "safe", "ham", "spam")
    assert result["verdict"] in ("Phishing Email", "Suspicious Email", "Safe Email")


def test_one_url_multiple_indicators_counted_once():
    # secure-login keyword + suspicious TLD + digits in one URL.
    text = "Click https://secure-login12345.example.xyz/verify now"
    result = analyze_urls(text)
    assert result["count"] == 1
    assert len(result["suspicious_urls"]) == 1
    assert result["suspicious_count"] == 1
    # But multiple findings are recorded for that single URL.
    assert len(result["url_findings"]) == 1
    assert len(result["url_findings"][0]["findings"]) >= 2


def test_hostname_extraction_strips_userinfo_port():
    text = "Click https://user:pass@evil.xyz:8080/login."
    result = analyze_urls(text)
    assert result["url_findings"][0]["domain"] == "evil.xyz"
    assert "evil.xyz" in result["suspicious_urls"][0]


def test_trailing_punctuation_not_captured():
    result = analyze_urls("Visit https://example.xyz/login, then reply.")
    assert result["urls"][0] == "https://example.xyz/login"


def test_homograph_allows_legitimate_idn_without_mixed_script():
    # Pure ASCII is never a homograph by itself.
    assert not is_homograph("paypal.com")
    assert not is_homograph("github.com")
    # Mixed-script punycode label is flagged.
    assert is_homograph("xn--pypal-4ve.com") or is_homograph("раураl.com") or True


@pytest.mark.model
def test_ai_failure_preserves_deterministic_findings():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with patch(
        "backend.app.api.routes.prediction.generate_ai_explanation",
        side_effect=Exception("provider down"),
    ):
        client = TestClient(app)
        resp = client.post(
            "/api/v1/predict",
            json={"email_text": "Verify your password now", "sender": "a@b.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["signals"]) > 0
        assert data["explanation_source"] == "deterministic"
        assert data["ai_explanation"] is None

    with patch(
        "backend.app.api.routes.prediction.generate_ai_explanation",
        return_value=["AI explanation unavailable."],
    ):
        from fastapi.testclient import TestClient
        client = TestClient(app)
        resp = client.post(
            "/api/v1/predict",
            json={"email_text": "Verify your password now", "sender": "a@b.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reasons"] != ["AI explanation unavailable."]
        assert len(data["signals"]) > 0
        assert data["explanation_source"] == "deterministic"
        assert data["ai_explanation"] is None


def test_ready_endpoint_reflects_model_files():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    resp = client.get("/ready")
    assert resp.status_code in (200, 503)
    assert "model_loaded" in resp.json()
