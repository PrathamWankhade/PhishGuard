import sys
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parents[3] / "ai-engine"
if str(ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(ENGINE_PATH))

from inference.predict import predict_email
from backend.app.services.explanation_engine import build_explanations
from backend.app.services.sender_analyzer import analyze_sender
from backend.app.services.url_analyzer import analyze_urls


VERDICT_POLICY_VERSION = "phase1-explicit-v1"

# Documented decision policy: risk_score is a heuristic policy score (0-100),
# NOT a calibrated probability. Thresholds below were chosen for Phase 1
# stability and must be re-validated on a held-out set (see Phase 2).
RISK_HIGH_THRESHOLD = 75
RISK_MEDIUM_THRESHOLD = 45


def classify_risk(risk_score: float) -> str:
    if risk_score >= RISK_HIGH_THRESHOLD:
        return "high"
    if risk_score >= RISK_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def verdict_for_risk(risk_level: str) -> str:
    return (
        "Phishing Email"
        if risk_level == "high"
        else "Suspicious Email"
        if risk_level == "medium"
        else "Safe Email"
    )


def detect_phishing(email_text: str, sender: str = "") -> dict:
    prediction = predict_email(email_text, sender)
    url_analysis = analyze_urls(email_text)
    sender_analysis = analyze_sender(sender)

    # Raw model output — never overwritten by heuristics.
    model_prediction = prediction["prediction"]
    model_confidence = prediction["confidence"]

    # Combined policy score. Unique suspicious-URL count (not rule-hit count).
    suspicious_count = url_analysis.get("suspicious_count", len(url_analysis.get("suspicious_urls", [])))
    url_risk = min(20, suspicious_count * 4)
    sender_risk = sender_analysis["risk"]
    risk_score = min(99, model_confidence + url_risk + sender_risk)

    risk_level = classify_risk(risk_score)
    label = verdict_for_risk(risk_level)

    result = {
        # Final verdict under the documented policy.
        "label": label,
        "verdict": label,
        # Raw model output, preserved untouched.
        "prediction": model_prediction,
        "model_prediction": model_prediction,
        "model_confidence": model_confidence,
        # Combined heuristic policy score — distinct from model probability.
        "risk_score": risk_score,
        "risk_level": risk_level,
        # Legacy field kept for existing UI/dashboard: now explicitly the
        # risk score, not the model probability. New clients should use
        # model_confidence / risk_score.
        "confidence": risk_score,
        "signals": build_explanations(prediction, url_analysis, sender_analysis),
        "reasons": build_explanations(prediction, url_analysis, sender_analysis),
        "source": "backend-ai-engine",
        "policy_version": VERDICT_POLICY_VERSION,
    }

    return result
