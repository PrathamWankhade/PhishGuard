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
    assert "phishing_probability" in result
    assert "risk_score" in result
    assert "risk_level" in result
    assert "verdict" in result
    assert "signals" in result
    # Legacy fields still present for UI compat.
    assert result["label"] == result["verdict"]
    assert result["prediction"] == result["model_prediction"]
    # Risk is a policy score built from phishing probability + evidence,
    # distinct from max-class confidence.
    assert 0 <= result["phishing_probability"] <= 1
    assert 0 <= result["risk_score"] <= 99


@pytest.mark.model
def test_confident_legitimate_is_not_phishing_by_score_alone():
    """P0 regression: model P(legitimate)=0.96 must not yield a phishing verdict.

    Mocks the classifier (no artifacts needed) and asserts the risk score
    starts from the phishing-class probability, not max-class confidence.
    """
    from unittest.mock import patch as _patch

    fake_prediction = {
        "label": "Safe Email",
        "prediction": "legitimate",
        "confidence": 96.0,
        "phishing_probability": 0.04,
        "risk_level": "low",
        "reasons": ["No strong phishing indicators found"],
        "source": "ml-model",
    }
    with _patch(
        "backend.app.services.phishing_detector.predict_email",
        return_value=fake_prediction,
    ):
        result = detect_phishing(
            "Hi team, please find the meeting notes attached. Best, John",
            "john@company.com",
        )
    assert result["model_prediction"] == "legitimate"
    assert result["phishing_probability"] == 0.04
    assert result["risk_score"] < 45
    assert result["verdict"] == "Safe Email"


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


def test_homograph_mixed_script_flagged():
    assert is_homograph("раураl.com")  # Cyrillic 'а' mixed with Latin 'l'
    assert is_homograph("secure-раyраl.com")


def test_homograph_legitimate_names_allowed():
    assert not is_homograph("paypal.com")
    assert not is_homograph("github.com")
    assert not is_homograph("münchen.de")  # accented Latin, single script
    assert not is_homograph("日本.jp")  # single non-Latin script IDN


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
    from pathlib import Path
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    resp = client.get("/ready")
    data = resp.json()
    assert "model_loaded" in data
    artifacts = (
        Path("trained_models/phishing_model.pkl").exists()
        and Path("trained_models/tfidf_vectorizer.pkl").exists()
    )
    if artifacts:
        # Artifacts present: readiness must actually verify them (would have
        # caught the wrong-base-path bug that only checked existence).
        assert resp.status_code == 200
        assert data["model_loaded"] is True
        assert "model_classes" in data
    else:
        assert resp.status_code == 503
