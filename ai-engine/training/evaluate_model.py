"""Model-level evaluation of the shipped artifacts on the holdout.

The split is byte-for-byte the one train_model.py trains against
(test_size=0.2, random_state=42, stratify=y on the same
final_emails.csv), so the rows scored here were never seen by the dumped
ensemble. Rebuild the dataset and the split moves -- re-run train_model.py
first, or this script silently scores the model on its own training rows.

Writes reports/evaluation_report.json (override with EVAL_REPORT_PATH).

Run:  python ai-engine/training/evaluate_model.py
"""
import os
import joblib
import pandas as pd
import json
import time

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    classification_report, log_loss, brier_score_loss, roc_auc_score,
    average_precision_score,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.environ.get("EVAL_DATASET_PATH", os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv"))
MODEL_PATH = os.environ.get("EVAL_MODEL_PATH", os.path.join(PROJECT_ROOT, "trained_models", "phishing_model.pkl"))
VECTORIZER_PATH = os.environ.get("EVAL_VECTORIZER_PATH", os.path.join(PROJECT_ROOT, "trained_models", "tfidf_vectorizer.pkl"))
REPORT_PATH = os.environ.get("EVAL_REPORT_PATH", os.path.join(PROJECT_ROOT, "reports", "evaluation_report.json"))

# Calibration and ranking metrics reported alongside accuracy.
CALIBRATION_BINS = 15
# Latency is sampled, not measured over the whole holdout: a per-row loop over
# ~39k emails would dwarf the actual scoring cost and produce a meaningless
# figure.
LATENCY_SAMPLE = 2000


def expected_calibration_error(y_true, proba, bins: int = CALIBRATION_BINS) -> float:
    """Expected calibration error (ECE): sample-weighted mean gap between
    confidence and accuracy across equal-width probability bins."""
    import numpy as np

    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(proba, edges) - 1, 0, bins - 1)
    n = len(proba)
    ece = 0.0
    for b in range(bins):
        mask = idx == b
        count = int(mask.sum())
        if not count:
            continue
        conf = float(proba[mask].mean())
        acc = float((y_true[mask] == 1).mean())
        ece += (count / n) * abs(acc - conf)
    return round(ece, 4)


def evaluate_model() -> dict:
    dataset = pd.read_csv(DATASET_PATH)
    X = dataset["email_text"]
    y = dataset["label"]

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    # Latency measured per request (vectorize + score), which is what an API
    # caller experiences; excludes model load and network reputation calls.
    # Sampled: a per-row loop over the whole holdout would dominate runtime.
    latency_sample = X_test.head(LATENCY_SAMPLE)
    latencies = []
    for text in latency_sample:
        t0 = time.perf_counter()
        model.predict_proba(vectorizer.transform([text]))
        latencies.append(time.perf_counter() - t0)
    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.50)]
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]

    X_test_tfidf = vectorizer.transform(X_test)
    predictions = model.predict(X_test_tfidf)
    proba = model.predict_proba(X_test_tfidf)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, pos_label="phishing")
    recall = recall_score(y_test, predictions, pos_label="phishing")
    f1 = f1_score(y_test, predictions, pos_label="phishing")

    y_binary = (y_test == "phishing").astype(int)
    phish_proba = proba[:, list(model.classes_).index("phishing")]
    y_binary_array = y_binary.to_numpy()
    phish_proba_array = phish_proba

    cm = confusion_matrix(y_test, predictions)
    report = classification_report(y_test, predictions, output_dict=True)

    # False-positive / false-negative rates (operational, not just accuracy).
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(float(fp / (fp + tn)) if (fp + tn) else 0.0, 4),
        "false_negative_rate": round(float(fn / (fn + tp)) if (fn + tp) else 0.0, 4),
        "log_loss": round(float(log_loss(y_binary, phish_proba)), 4),
        "brier_score": round(float(brier_score_loss(y_binary, phish_proba)), 4),
        # Ranking quality. PR-AUC matters more than ROC-AUC here: the phishing
        # class is a minority in production traffic.
        "roc_auc": round(float(roc_auc_score(y_binary_array, phish_proba_array)), 4),
        "pr_auc": round(float(average_precision_score(y_binary_array, phish_proba_array)), 4),
        # Calibration: are the probabilities honest numbers?
        "expected_calibration_error": expected_calibration_error(y_binary_array, phish_proba_array),
        "latency_ms": {"p50": round(p50 * 1000, 1), "p95": round(p95 * 1000, 1)},
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }

    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"Saved: {REPORT_PATH}")
    return metrics


if __name__ == "__main__":
    evaluate_model()