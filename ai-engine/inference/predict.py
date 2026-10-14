from pathlib import Path
import joblib
import re

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = BASE_DIR / "trained_models" / "phishing_model.pkl"
VECTORIZER_PATH = BASE_DIR / "trained_models" / "tfidf_vectorizer.pkl"

_model = None
_vectorizer = None


def _load_models():
    global _model, _vectorizer
    if _model is None:
        print("Loading ML model...")
        _model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
        print("Model loaded!")
    return _model, _vectorizer


SUSPICIOUS_TERMS = [
    "urgent", "verify", "password", "otp", "bank", "suspended",
    "click", "login", "payment", "limited", "account", "immediately",
    "security", "update", "confirm", "restricted", "blocked",
    "unauthorized", "unusual", "activity", "alert", "warning",
    "compromised", "required", "attention", "action required",
    "reactivate", "deactivate", "deactivated",
    "credit card", "debit card", "ssn", "social security",
    "routing number", "wire transfer", "western union",
    "money gram", "gift card", "cryptocurrency", "bitcoin",
    "investment", "guaranteed", "prize", "winner", "lottery",
    "inheritance", "donation", "charity", "funds",
    "overdue", "past due", "invoice", "statement",
    "confidential", "internal", "exclusive", "limited time",
    "expires", "expiration", "valid until",
]

SUSPICIOUS_TLDS = {"xyz", "top", "click", "zip", "ru", "cn", "tk", "ml", "ga", "cf", "gq"}
HOMOGRAPH_CHARS = set("ɑаеéеооссррххијїąæçđęėįłøőœųūż")


def contains_homograph(text: str) -> bool:
    return any(c in HOMOGRAPH_CHARS for c in text.lower())


def generate_reasons(email_text: str, sender: str) -> list:
    reasons = []
    text_lower = email_text.lower()
    sender_lower = sender.lower()

    matched = [term for term in SUSPICIOUS_TERMS if term in text_lower]
    if matched:
        top_terms = matched[:6]
        reasons.append(f"Suspicious keywords detected ({len(matched)}): {', '.join(top_terms)}")

    url_count = len(re.findall(r"https?://|www\.", email_text))
    if url_count:
        reasons.append(f"{url_count} URL(s) found in email body")

    shortened = re.findall(r"(bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly)", text_lower)
    if shortened:
        reasons.append(f"URL shortener detected: {shortened[0]}")

    ip_urls = re.findall(r"https?://\d+\.\d+\.\d+\.\d+", text_lower)
    if ip_urls:
        reasons.append("IP-based URL detected (attempts to bypass domain filtering)")

    suspicious_tld_match = re.search(r"\.(" + "|".join(SUSPICIOUS_TLDS) + r")\b", sender_lower)
    if suspicious_tld_match:
        reasons.append(f"Suspicious sender TLD: .{suspicious_tld_match.group(1)}")

    if contains_homograph(email_text + sender):
        reasons.append("Possible homograph attack detected (lookalike characters)")

    if re.search(r"(verify|confirm|reset|update).*(password|account|login|credential)", text_lower):
        reasons.append("Credential harvesting attempt: requests password/account verification")

    urgency_phrases = ["immediately", "within 24 hours", "expires", "limited time", "act now", "suspended", "blocked"]
    if any(p in text_lower for p in urgency_phrases):
        reasons.append("Urgency language detected: pressures recipient to act quickly")

    if not reasons:
        reasons.append("No strong phishing indicators found")

    return reasons


def predict_email(email_text: str, sender: str = "") -> dict:
    model, vectorizer = _load_models()

    text = email_text + " " + sender
    vectorized = vectorizer.transform([text])

    prediction = model.predict(vectorized)[0]
    probabilities = model.predict_proba(vectorized)[0]
    classes = list(model.classes_)
    # Phishing-class probability: the model's estimate that THIS email is
    # phishing. Distinct from max-class confidence below.
    phishing_probability = round(float(probabilities[classes.index("phishing")]), 4)
    confidence = round(max(probabilities) * 100, 2)

    if confidence >= 75:
        risk_level = "high"
    elif confidence >= 50:
        risk_level = "medium"
    else:
        risk_level = "low"

    label = "Phishing Email" if prediction == "phishing" else "Safe Email"
    reasons = generate_reasons(email_text, sender)

    return {
        "label": label,
        "prediction": prediction,
        "confidence": confidence,
        "phishing_probability": phishing_probability,
        "risk_level": risk_level,
        "reasons": reasons,
        "source": "ml-model",
    }
