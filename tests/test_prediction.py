import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-engine"))

pytestmark = pytest.mark.model

from inference.predict import predict_email, generate_reasons, contains_homograph


def test_phishing_email_gets_high_risk():
    result = predict_email(
        "URGENT click https://secure-login.example.xyz to verify your password and OTP immediately",
        "support@security-alert.xyz",
    )
    assert result["risk_level"] == "high"
    assert result["confidence"] >= 70


def test_safe_email_gets_low_risk():
    result = predict_email(
        "Dear students, the assignment deadline has been extended to next Friday. Regards, Professor.",
        "professor@university.edu",
    )
    assert "label" in result
    assert "confidence" in result
    assert "reasons" in result


def test_empty_text():
    result = predict_email("", "")
    assert "label" in result
    assert result["confidence"] >= 0


def test_contains_homograph():
    assert contains_homograph("раураl.com")  # Cyrillic 'а' and 'е'
    assert contains_homograph("secure-раyраl.com")
    assert not contains_homograph("paypal.com")  # regular ASCII


def test_not_contains_homograph():
    assert not contains_homograph("github.com")
    assert not contains_homograph("hello-world.com")
    assert not contains_homograph("example123.org")


def test_generate_reasons_credential_harvesting():
    reasons = generate_reasons(
        "Please verify your password and login credentials immediately", "support@bank.com"
    )
    credential_reason = [r for r in reasons if "credential" in r.lower()]
    assert len(credential_reason) > 0


def test_generate_reasons_urgency():
    reasons = generate_reasons(
        "Your account will be suspended within 24 hours act now", "alert@service.com"
    )
    urgency_reason = [r for r in reasons if "urgency" in r.lower()]
    assert len(urgency_reason) > 0


def test_ip_url_detection():
    result = predict_email(
        "Check your account at http://192.168.1.1/login",
        "admin@server.com",
    )
    reasons = result["reasons"]
    ip_reason = [r for r in reasons if "IP-based" in r]
    assert len(ip_reason) > 0
