"""Inference-contract tests: run against REAL artifacts locally and against the
deterministic fixture model in CI (see integration job). No behavioral
accuracy claims — only that the contract holds end to end."""
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

pytestmark = pytest.mark.model

client = TestClient(app)


def test_ready_reports_phishing_class():
    r = client.get("/ready")
    assert r.status_code == 200
    assert "phishing" in r.json()["model_classes"]


def test_predict_contract_fields():
    r = client.post(
        "/api/v1/predict",
        json={"email_text": "Verify your account now", "sender": "a@b.com"},
    )
    assert r.status_code == 200
    data = r.json()
    for field in ("status", "label", "verdict", "model_prediction",
                  "model_confidence", "phishing_probability", "risk_score",
                  "risk_level", "signals", "reasons"):
        assert field in data, f"missing {field}"
    assert data["status"] == "completed"
    assert 0.0 <= data["phishing_probability"] <= 1.0
    assert isinstance(data["signals"], list) and len(data["signals"]) > 0
    mapping = {"high": "Phishing Email", "medium": "Suspicious Email", "low": "Safe Email"}
    assert data["verdict"] == mapping[data["risk_level"]]


def test_upload_contract():
    raw = b"From: boss@company.com\r\nSubject: hello\r\n\r\nPlease review the notes."
    r = client.post("/api/v1/upload", files={"file": ("a.eml", raw, "message/rfc822")})
    assert r.status_code == 200
    assert r.json()["sender"] == "boss@company.com"
