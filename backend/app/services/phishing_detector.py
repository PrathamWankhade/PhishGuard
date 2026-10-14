import sys
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parents[3] / "ai-engine"
if str(ENGINE_PATH) not in sys.path:
    sys.path.insert(0, str(ENGINE_PATH))

from inference.predict import predict_email
from backend.app.services.explanation_engine import build_explanations
from backend.app.services.sender_analyzer import analyze_sender
from backend.app.services.url_analyzer import analyze_urls
from backend.app.services.auth_analyzer import analyze_auth
from backend.app.services.bec_analyzer import analyze_bec


VERDICT_POLICY_VERSION = "phase4-probability-v3"

# Documented decision policy: risk_score is a heuristic policy score (0-100),
# NOT a calibrated probability. v3 bases model risk on the PHISHING-CLASS
# probability (not max-class confidence: a 96% legitimate prediction must
# contribute ~4 points, not 96). Thresholds below are interim and must be
# re-validated on a held-out set with legitimate-but-suspicious emails.
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


def detect_phishing(
    email_text: str,
    sender: str = "",
    reply_to: str = "",
    return_path: str = "",
    auth_results: str = "",
) -> dict:
    prediction = predict_email(email_text, sender)
    url_analysis = analyze_urls(email_text)
    sender_analysis = analyze_sender(sender)
    auth_analysis = analyze_auth(sender, reply_to, return_path, auth_results)
    bec_analysis = analyze_bec(email_text, sender)

    # Raw model output — never overwritten by heuristics.
    model_prediction = prediction["prediction"]
    model_confidence = prediction["confidence"]
    phishing_probability = float(prediction.get("phishing_probability", 0.0))

    # Combined policy score. Model risk comes from the PHISHING-CLASS
    # probability: confident-legitimate mail contributes ~0, not ~100.
    # Unique suspicious-URL count (not rule-hit count).
    model_risk = phishing_probability * 100
    suspicious_count = url_analysis.get("suspicious_count", len(url_analysis.get("suspicious_urls", [])))
    url_risk = min(20, suspicious_count * 4)
    sender_risk = sender_analysis["risk"]
    # New evidence channels are bounded so they can tip borderline cases but
    # never fabricate certainty on their own.
    evidence_risk = min(10, auth_analysis["risk"] + bec_analysis["risk"])
    risk_score = min(99, round(model_risk + url_risk + sender_risk + evidence_risk, 2))

    risk_level = classify_risk(risk_score)
    label = verdict_for_risk(risk_level)

    signals = (
        build_explanations(prediction, url_analysis, sender_analysis)
        + auth_analysis.get("reasons", [])
        + bec_analysis.get("reasons", [])
    )

    result = {
        # Final verdict under the documented policy.
        "label": label,
        "verdict": label,
        # Raw model output, preserved untouched.
        "prediction": model_prediction,
        "model_prediction": model_prediction,
        "model_confidence": model_confidence,
        "phishing_probability": phishing_probability,
        # Combined heuristic policy score — distinct from model probability.
        "risk_score": risk_score,
        "risk_level": risk_level,
        # Legacy field kept for existing UI/dashboard: now explicitly the
        # risk score, not the model probability. New clients should use
        # model_confidence / risk_score.
        "confidence": risk_score,
        "signals": signals,
        "reasons": signals,
        "source": "backend-ai-engine",
        "policy_version": VERDICT_POLICY_VERSION,
    }

    return result
