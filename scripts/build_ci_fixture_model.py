"""Build a DETERMINISTIC toy model for CI integration tests.

NOT a production artifact: 40 hand-written emails, TF-IDF + LogisticRegression,
fixed seed. Lets CI exercise the real inference contract (vectorize ->
predict_proba -> phishing class -> /ready, /predict) without the 195k-mail
dataset. Never commit its outputs; the CI job regenerates them every run.

Run:  python scripts/build_ci_fixture_model.py
"""
import os

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(PROJECT_ROOT, "trained_models")

PHISH = [
    "urgent verify your password now click link",
    "account suspended confirm login immediately",
    "wire transfer invoice overdue payment now",
    "claim prize winner lottery send fee",
    "security alert unusual activity verify account",
    "password expired reset credentials click here",
    "bank locked confirm identity otp code",
    "gift card payment required urgently",
    "inheritance funds release send details",
    "login attempt blocked verify now",
    "update payment method immediately limited time",
    "confidential wire instruction do not tell",
    "ceo request transfer funds discreetly",
    "suspended mailbox reactivate click link",
    "cryptocurrency investment guaranteed returns",
    "debit card compromised confirm pin",
    "tax refund claim submit details now",
    "delivery failed confirm address paying fee",
    "social security suspended verify identity",
    "free trial expires confirm credit card",
]
LEGIT = [
    "meeting notes attached thanks team",
    "lunch tomorrow at noon see you",
    "project deadline extended next friday",
    "reminder dentist appointment thursday",
    "quarterly report draft for review",
    "happy birthday wishes weekend plans",
    "order shipped tracking number included",
    "newsletter weekly digest unsubscribe link",
    "invoice receipt for your records paid",
    "team outing photos shared folder",
    "conference agenda attached regards",
    "homework solutions posted portal",
    "flight itinerary confirmation details",
    "recipe exchange weekend barbecue",
    "book club selection next month",
    "gym schedule updated classes",
    "weather alert campus closing early",
    "library hours extended finals week",
    "parking permit renewal notice",
    "volunteer signup sheet attached",
]


def main() -> None:
    texts = PHISH + LEGIT
    labels = ["phishing"] * len(PHISH) + ["legitimate"] * len(LEGIT)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", max_features=500)),
        ("clf", LogisticRegression(max_iter=2000, random_state=42)),
    ])
    pipeline.fit(texts, labels)
    os.makedirs(MODEL_DIR, exist_ok=True)
    # predict.py expects (model, vectorizer) separately: persist the fitted steps.
    joblib.dump(pipeline.named_steps["clf"], os.path.join(MODEL_DIR, "phishing_model.pkl"))
    joblib.dump(pipeline.named_steps["tfidf"], os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
    import json

    meta = {"fixture": True, "seed": 42, "rows": len(texts), "note": "CI-only toy model, not for release"}
    with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"Fixture model written to {MODEL_DIR}")


if __name__ == "__main__":
    main()
