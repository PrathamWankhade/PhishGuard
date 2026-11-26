"""Threshold analysis for the phishing decision policy.

Two things are swept, because they are NOT interchangeable:

  1. `p_phishing`   -- the model probability alone.
  2. `risk_score`   -- the shipped policy score (probability + URL/sender/
                       evidence bonuses, capped 99), which is what the
                       75/45 product thresholds actually compare against.

Sweeping only the probability tells you how well the model ranks; sweeping the
risk score tells you what the product decides. A threshold chosen on one does
not transfer to the other.

The current policy (RISK_HIGH_THRESHOLD=75, RISK_MEDIUM_THRESHOLD=45) is the
shipped product contract. This script REPORTS operating points; it never
changes them. Changing a deployed threshold is a separate decision that owns
the consequences on live traffic.

Run:  python ai-engine/training/threshold_analysis.py
"""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "ai-engine"))

from backend.app.services.phishing_detector import (  # noqa: E402
    RISK_HIGH_THRESHOLD, RISK_MEDIUM_THRESHOLD, classify_risk, compute_risk_score,
)
from backend.app.services.auth_analyzer import analyze_auth  # noqa: E402
from backend.app.services.bec_analyzer import analyze_bec  # noqa: E402
from backend.app.services.sender_analyzer import analyze_sender  # noqa: E402
from backend.app.services.url_analyzer import analyze_urls  # noqa: E402

DATASET_PATH = os.environ.get("THRESH_DATASET_PATH", os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv"))
MODEL_PATH = os.environ.get("THRESH_MODEL_PATH", os.path.join(PROJECT_ROOT, "trained_models", "phishing_model.pkl"))
VECTORIZER_PATH = os.environ.get("THRESH_VECTORIZER_PATH", os.path.join(PROJECT_ROOT, "trained_models", "tfidf_vectorizer.pkl"))
REPORT_PATH = os.environ.get("THRESH_REPORT_PATH", os.path.join(PROJECT_ROOT, "reports", "threshold_analysis.json"))

POSITIVE, NEGATIVE = 1, 0


def to_binary(y_true) -> np.ndarray:
    """Accept {0,1}, {False,True}, {'legitimate','phishing'} or booleans.

    The sketch in the original roadmap used precision_score(..., average='binary')
    directly on string labels, which raises instead of reporting; normalising
    here keeps one code path.
    """
    if isinstance(y_true, pd.Series):
        y_true = y_true.to_numpy()
    arr = np.asarray(list(y_true))
    if arr.dtype == bool:
        return arr.astype(int)
    if np.issubdtype(arr.dtype, np.number):
        return arr.astype(int)
    mapping = {"phishing": 1, "legitimate": 0, "safe": 0, "spam": 1, "ham": 0}
    out = [mapping.get(str(v).strip().lower()) for v in arr]
    if any(v is None for v in out):
        raise ValueError(f"Unrecognised labels: {sorted({str(v) for v in arr if str(v).lower() not in mapping})}")
    return np.asarray(out, dtype=int)


def _rates(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Rates computed from the confusion matrix, so precision/recall and the
    FPR/FNR accounting can never disagree."""
    cm = confusion_matrix(y_true, y_pred, labels=[NEGATIVE, POSITIVE])
    tn, fp, fn, tp = (int(v) for v in cm.ravel())
    return {
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "n": int(len(y_true)),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        # A threshold that flags everything has zero positive predictions of
        # the phishing class; precision is undefined, reported as 0.0 rather
        # than raising zero_division or silently as 1.0.
        "precision": round(tp / (tp + fp), 6) if (tp + fp) else 0.0,
        "recall": round(tp / (tp + fn), 6) if (tp + fn) else 0.0,
        "f1": round(2 * tp / (2 * tp + fp + fn), 6) if (2 * tp + fp + fn) else 0.0,
        "fpr": round(fp / (fp + tn), 6) if (fp + tn) else 0.0,
        "fnr": round(fn / (fn + tp), 6) if (fn + tp) else 0.0,
        "flagged": round((tp + fp) / len(y_true), 6),
    }


def evaluate_thresholds(y_true, scores, thresholds=None) -> list:
    """Operating points for every threshold, plus the shipped policy point."""
    y_true = to_binary(y_true)
    scores = np.asarray(scores, dtype=float)
    if thresholds is None:
        thresholds = np.arange(0.10, 1.01, 0.05)

    rows = []
    for t in thresholds:
        rows.append({"threshold": round(float(t), 4), **_rates(y_true, (scores >= t).astype(int))})
    return rows


def select_threshold(y_true, scores, *, target_recall=None, min_precision=None,
                     thresholds=None) -> dict:
    """Pick an operating point from the sweep.

    - target_recall:  the LOWEST threshold that still reaches it (keeps as much
      precision as possible while covering the recall floor). If unattainable,
      returns the highest-recall point and says so.
    - min_precision:  the HIGHEST threshold that still clears it (maximises
      recall without trading away precision).
    - neither:        F1-optimal threshold.

    Recall floors should come from validated operational cost, not from the
    sweep itself -- choosing on this data and reporting on it is tuning on the
    test set.
    """
    rows = evaluate_thresholds(y_true, scores, thresholds)

    if target_recall is not None:
        ok = [r for r in rows if r["recall"] >= target_recall]
        if not ok:
            best = max(rows, key=lambda r: (r["recall"], -r["fp"]))
            return {**best, "attainable": False,
                    "detail": f"no threshold reaches recall {target_recall}"}
        best = min(ok, key=lambda r: r["threshold"])
        return {**best, "attainable": True, "objective": f"target_recall>={target_recall}"}

    if min_precision is not None:
        ok = [r for r in rows if r["precision"] >= min_precision]
        if not ok:
            best = max(rows, key=lambda r: r["precision"])
            return {**best, "attainable": False,
                    "detail": f"no threshold reaches precision {min_precision}"}
        best = max(ok, key=lambda r: (r["threshold"], r["recall"]))
        return {**best, "attainable": True, "objective": f"min_precision>={min_precision}"}

    return {**max(rows, key=lambda r: r["f1"]), "attainable": True, "objective": "max_f1"}


def _policy_risk_scores(test_df: pd.DataFrame, proba) -> list:
    """Text-only policy scores using the SHIPPED formula.

    Mirrors scripts/validate_policy.py exactly: empty sender, empty header
    evidence, so the two reports describe the same policy on the same rows.
    That measures the policy on text alone -- sender/header effects are covered
    by unit tests, and a sender-bearing sweep needs a different dataset.
    """
    sender_risk = analyze_sender("")["risk"]
    auth_risk = analyze_auth("", "", "", "")["risk"]

    scores = []
    for (text,), p in zip(test_df[["email_text"]].itertuples(index=False), proba):
        urls = analyze_urls(text)
        bec = analyze_bec(text, "")
        scores.append(compute_risk_score(p, urls, sender_risk, auth_risk, bec["risk"]))
    return scores


def main() -> dict:
    df = pd.read_csv(DATASET_PATH)
    _, test = train_test_split(df, test_size=0.2, random_state=42, stratify=df["label"])
    model = joblib.load(MODEL_PATH)
    vec = joblib.load(VECTORIZER_PATH)

    proba = model.predict_proba(vec.transform(test["email_text"]))[:, list(model.classes_).index("phishing")]
    y = to_binary(test["label"])
    risk_scores = _policy_risk_scores(test, proba)

    # The shipped policy point, measured on the same rows.
    shipped = _rates(y, np.asarray([1 if classify_risk(s) == "high" else 0 for s in risk_scores]))
    shipped_suspicious = _rates(
        y, np.asarray([1 if classify_risk(s) in ("high", "medium") else 0 for s in risk_scores])
    )

    # Sweeps. Probability is in [0,1]; risk score in [0,99] so its grid is scaled.
    prob_thresholds = np.arange(0.10, 1.01, 0.05)
    risk_thresholds = np.arange(10, 100, 5, dtype=float)

    report = {
        "n": int(len(y)),
        "policy": {
            "version_note": "reported from thresholds, not a change to them",
            "high_threshold": RISK_HIGH_THRESHOLD,
            "medium_threshold": RISK_MEDIUM_THRESHOLD,
            "shipped_as_phishing_high": shipped,
            "shipped_as_phishing_or_suspicious": shipped_suspicious,
        },
        "sweep_probability": evaluate_thresholds(y, proba, prob_thresholds),
        "sweep_risk_score": evaluate_thresholds(y, risk_scores, risk_thresholds),
        "examples": {
            "risk_target_recall_0_95": select_threshold(y, risk_scores, target_recall=0.95,
                                                        thresholds=risk_thresholds),
            "risk_min_precision_0_98": select_threshold(y, risk_scores, min_precision=0.98,
                                                        thresholds=risk_thresholds),
            "prob_max_f1": select_threshold(y, proba, thresholds=prob_thresholds),
        },
        "caveats": [
            "Thresholds are selected on the same rows they are reported on; that is "
            "tuning on the test set. Use a validation carve from the TRAINING side to "
            "choose, and report once here.",
            "probability and risk_score are different quantities: a threshold chosen "
            "on the probability sweep does not transfer to the 75/45 product policy.",
            "risk scores are text-only (empty sender, no header evidence), matching "
            "scripts/validate_policy.py.",
        ],
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report["policy"], indent=2))
    print(json.dumps(report["examples"], indent=2))
    print(f"Saved: {REPORT_PATH}")
    return report


if __name__ == "__main__":
    main()