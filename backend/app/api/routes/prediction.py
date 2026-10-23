import hashlib
import json
import re

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.openrouter_explainer import generate_ai_explanation
from backend.app.services.phishing_detector import detect_phishing
from backend.app.database.db import get_connection

router = APIRouter()


class PredictionRequest(BaseModel):
    email_text: str
    sender: str = ""
    reply_to: str = ""
    return_path: str = ""
    auth_results: str = ""


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:10000]


@router.post("/predict")
def predict_email(request: PredictionRequest):
    from fastapi import HTTPException

    safe_text = sanitize_text(request.email_text)
    safe_sender = sanitize_text(request.sender)[:500]
    safe_reply = sanitize_text(request.reply_to)[:500]
    safe_bounce = sanitize_text(request.return_path)[:500]
    safe_auth = sanitize_text(request.auth_results)[:2000]

    if not safe_text.strip():
        raise HTTPException(status_code=422, detail="email_text must not be empty.")

    # NOTE: auth evidence from this public endpoint is ALWAYS untrusted
    # (caller-supplied, forgeable). There is deliberately no request field
    # that lets a client mark its own headers trusted — trusted results only
    # come from receiving infrastructure (see auth_analyzer TRUST BOUNDARY).
    result = detect_phishing(safe_text, safe_sender, safe_reply, safe_bounce, safe_auth)

    # Deterministic findings are the source of truth and are never replaced.
    deterministic_reasons: list = list(result.get("reasons", []))

    try:
        ai_reasons = generate_ai_explanation(safe_text, safe_sender, result["label"], result["risk_score"])
    except Exception:
        ai_reasons = None
    if ai_reasons and ai_reasons != ["AI explanation unavailable."]:
        result["ai_explanation"] = ai_reasons
        result["explanation_source"] = "ai"
    else:
        result["ai_explanation"] = None
        result["explanation_source"] = "deterministic"
    result["signals"] = deterministic_reasons
    result["reasons"] = deterministic_reasons
    result["status"] = "completed"

    # Structured SHA-256 dedup key with explicit field boundaries
    # (v1 namespace + NUL separators), so sender/text mixes cannot collide.
    email_hash = hashlib.sha256(
        ("v1\0" + safe_text.strip().lower() + "\0" + safe_sender.strip().lower()).encode()
    ).hexdigest()

    result["email_hash"] = email_hash

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, scan_count FROM scan_history WHERE email_hash = ?", (email_hash,))
    existing = cursor.fetchone()

    reasons_json = json.dumps(deterministic_reasons)

    if existing:
        cursor.execute("""
            UPDATE scan_history
            SET sender=?, prediction=?, confidence=?, risk_level=?, reasons=?,
                scan_count=scan_count+1, created_at=CURRENT_TIMESTAMP
            WHERE email_hash=?
        """, (safe_sender, result["label"], result["risk_score"], result["risk_level"], reasons_json, email_hash))
    else:
        cursor.execute("""
            INSERT INTO scan_history (email_hash, sender, email_text, prediction, confidence, risk_level, reasons, scan_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (email_hash, safe_sender, safe_text, result["label"], result["risk_score"], result["risk_level"], reasons_json))

    conn.commit()
    conn.close()

    return result
