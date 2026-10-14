import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.mark.model
def test_predict_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={"email_text": "URGENT verify your password at https://login.example.xyz", "sender": "alert@example.xyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in {"medium", "high"}
    assert "confidence" in data
    assert "reasons" in data
    assert len(data["reasons"]) > 0


@pytest.mark.model
def test_predict_safe_email():
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={"email_text": "Hi team, please find the meeting notes attached. Best, John", "sender": "john@company.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data


def test_predict_empty_text():
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={"email_text": "", "sender": "test@test.com"},
    )
    assert response.status_code == 422


@pytest.mark.model
def test_predict_missing_sender():
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={"email_text": "URGENT click here to claim your prize"},
    )
    assert response.status_code == 200


@pytest.mark.model
def test_predict_header_evidence_surfaces_as_signal():
    client = TestClient(app)
    response = client.post(
        "/api/v1/predict",
        json={
            "email_text": "Please review the attached invoice.",
            "sender": "billing@company.com",
            "reply_to": "billing@company-support.xyz",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert any("Reply-To" in s for s in data["signals"])


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()
