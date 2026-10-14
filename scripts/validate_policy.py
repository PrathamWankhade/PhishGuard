"""Validate decision-policy thresholds on a held-out split.

Uses the SAME split protocol as training (stratified 80/20, seed 42) and the
shipped artifacts. Reports policy-level (verdict) precision/recall/FPR/FNR so
thresholds are measured, not assumed. Sender-dependent channels use an empty
sender here (text-only validation); header-evidence effects are covered by
unit tests.

Run:  python scripts/validate_policy.py   (writes reports/policy_validation.json)
"""
import json
import os
import sys

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ai-engine"))

from backend.app.services.phishing_detector import classify_risk, verdict_for_risk
from backend.app.services.url_analyzer import analyze_urls
from backend.app.services.sender_analyzer import analyze_sender
from backend.app.services.auth_analyzer import analyze_auth
from backend.app.services.bec_analyzer import analyze_bec

REPORT = os.path.join(PROJECT_ROOT, "reports", "policy_validation.json")


def main() -> None:
    df = pd.read_csv(os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv"))
    _, test = train_test_split(
        df, test_size=0.2, random_state=42, stratify=df["label"]
    )
    model = joblib.load(os.path.join(PROJECT_ROOT, "trained_models", "phishing_model.pkl"))
    vec = joblib.load(os.path.join(PROJECT_ROOT, "trained_models", "tfidf_vectorizer.pkl"))

    texts = (test["email_text"] + " ").tolist()
    proba = model.predict_proba(vec.transform(texts))[:, list(model.classes_).index("phishing")]

    y_true, y_verdict, scores = [], [], []
    for (text, label), p in zip(test[["email_text", "label"]].itertuples(index=False), proba):
        urls = analyze_urls(text)
        sender_a = analyze_sender("")
        auth_a = analyze_auth("", "", "", "")
        bec_a = analyze_bec(text, "")
        risk = min(99, round(
            float(p) * 100
            + min(20, urls.get("suspicious_count", 0) * 4)
            + sender_a["risk"]
            + min(10, auth_a["risk"] + bec_a["risk"]),
            2,
        ))
        y_true.append(1 if label == "phishing" else 0)
        y_verdict.append(verdict_for_risk(classify_risk(risk)))
        scores.append(risk)

    tp = sum(1 for t, v in zip(y_true, y_verdict) if t == 1 and v == "Phishing Email")
    fp = sum(1 for t, v in zip(y_true, y_verdict) if t == 0 and v == "Phishing Email")
    fn = sum(1 for t, v in zip(y_true, y_verdict) if t == 1 and v != "Phishing Email")
    tn = len(y_true) - tp - fp - fn
    report = {
        "n": len(y_true),
        "policy": "phase4-probability-v3, thresholds 75/45, text-only (sender='')",
        "policy_precision": round(tp / (tp + fp), 4) if tp + fp else 0.0,
        "policy_recall": round(tp / (tp + fn), 4) if tp + fn else 0.0,
        "policy_fpr": round(fp / (fp + tn), 4) if fp + tn else 0.0,
        "policy_fnr": round(fn / (fn + tp), 4) if fn + tp else 0.0,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
    }
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
