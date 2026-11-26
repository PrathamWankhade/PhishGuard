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
# contribute ~4 points, not 96). Thresholds measured on the 39,148-mail
# text-only holdout (reports/policy_validation.json): precision 99.5%,
# recall 93.3%, FPR 0.4%, FNR 6.7%. Re-validate with sender/header context
# and on source-separated data before changing them.
RISK_HIGH_THRESHOLD = 75
RISK_MEDIUM_THRESHOLD = 45


def compute_risk_score(
    phishing_probability: float,
    url_analysis: dict,
    sender_risk: float,
    auth_risk: float,
    bec_risk: float,
) -> float:
    """Authoritative implementation of the policy risk formula.

        risk = min(99, round(phishing_probability * 100 + url_risk
                             + sender_risk + evidence_risk, 2))

    - model term uses the PHISHING-CLASS probability, so confident-legitimate
      mail contributes ~0 rather than ~100 (max-class confidence would invert
      this).
    - url_risk is capped at 20 from the UNIQUE suspicious-URL count.
    - sender_risk is passed in from the sender analyser (capped at 30 there).
    - evidence_risk is capped at 10 across auth + BEC combined, so new
      channels can tip borderline cases but never fabricate certainty alone.

    Every consumer must call this rather than re-deriving the formula:
    scripts/validate_policy.py used to inline its own copy, which meant a
    policy change would silently leave the validated report describing a
    formula that is no longer shipped.
    """
    model_risk = float(phishing_probability) * 100
    suspicious_count = url_analysis.get(
        "suspicious_count", len(url_analysis.get("suspicious_urls", []))
    )
    url_risk = min(20, suspicious_count * 4)
    evidence_risk = min(10, float(auth_risk) + float(bec_risk))
    return min(99, round(model_risk + url_risk + float(sender_risk) + evidence_risk, 2))


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
    # Strict contract: a missing/invalid phishing probability must fail
    # loudly, never silently become a safe-looking zero.
    if "phishing_probability" not in prediction:
        raise RuntimeError("Inference result missing phishing_probability; refusing to score.")
    phishing_probability = float(prediction["phishing_probability"])
    if not 0.0 <= phishing_probability <= 1.0:
        raise RuntimeError(f"Invalid phishing_probability {phishing_probability}; refusing to score.")

    # Combined policy score. Single authoritative formula — see
    # compute_risk_score, which the validation scripts also call.
    risk_score = compute_risk_score(
        phishing_probability, url_analysis, sender_analysis["risk"],
        auth_analysis["risk"], bec_analysis["risk"],
    )

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
        # NOTE: no `confidence` alias here on purpose. A field named
        # "confidence" that actually carries the policy risk score is exactly
        # the model-probability/risk-score conflation this contract forbids;
        # clients must read `risk_score` (policy) or `model_confidence` /
        # `phishing_probability` (model).
        "signals": signals,
        "reasons": signals,
        "source": "backend-ai-engine",
        "policy_version": VERDICT_POLICY_VERSION,
    }

    return result
