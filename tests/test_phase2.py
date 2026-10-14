"""Phase 2 regression tests: dataset dedup, parser, upload, dashboard semantics."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.utils.email_parser import parse_raw_email


def test_parser_multipart_plain_preferred():
    raw = (
        "From: attacker@evil.xyz\r\n"
        "Subject: Verify now\r\n"
        "Content-Type: multipart/alternative; boundary=XYZ\r\n\r\n"
        "--XYZ\r\nContent-Type: text/plain\r\n\r\nHello, verify your password.\r\n"
        "--XYZ\r\nContent-Type: text/html\r\n\r\n<html>Click</html>\r\n--XYZ--"
    )
    out = parse_raw_email(raw)
    assert out["sender"] == "attacker@evil.xyz"
    assert out["subject"] == "Verify now"
    assert "verify your password" in out["body"]


def test_parser_malformed_never_raises():
    out = parse_raw_email("From: broken\nNo blank line, no MIME\nhttp://evil.xyz/x")
    assert "sender" in out and "body" in out
    assert isinstance(out["errors"], list)


def test_parser_extracts_urls_and_attachments():
    raw = (
        "From: a@b.com\r\nSubject: hi\r\n"
        "Content-Type: multipart/mixed; boundary=B\r\n\r\n"
        "--B\r\nContent-Type: text/plain\r\n\r\nSee https://evil.xyz/login\r\n"
        "--B\r\nContent-Type: application/octet-stream\r\n"
        "Content-Disposition: attachment; filename=\"bill.pdf\"\r\n\r\nABC\r\n--B--"
    )
    out = parse_raw_email(raw)
    assert any("evil.xyz" in u for u in out["urls"])
    assert out["attachments"] and out["attachments"][0]["filename"] == "bill.pdf"


def test_upload_rejects_bad_extension_and_oversize():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    r = client.post("/api/v1/upload", files={"file": ("evil.exe", b"hi", "application/octet-stream")})
    assert r.status_code == 415
    r = client.post("/api/v1/upload", files={"file": ("a.eml", b"   ", "message/rfc822")})
    assert r.status_code == 422


def test_upload_parses_eml():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    raw = b"From: boss@company.com\r\nSubject: hello\r\n\r\nPlease review the notes."
    r = client.post("/api/v1/upload", files={"file": ("a.eml", raw, "message/rfc822")})
    assert r.status_code == 200
    assert r.json()["sender"] == "boss@company.com"


def test_dashboard_counts_suspicious_and_events():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    # Ensure at least one scan of each class exists in test DB.
    client.post("/api/v1/predict", json={"email_text": "Meeting notes attached, thanks.", "sender": "a@company.com"})
    r = client.get("/api/v1/dashboard")
    assert r.status_code == 200
    data = r.json()
    assert "suspicious_count" in data
    assert "total_scan_events" in data and "unique_emails" in data
    assert data["phishing_count"] + data["suspicious_count"] + data["safe_count"] <= data["unique_emails"]
    assert data["total_scan_events"] >= data["unique_emails"]
