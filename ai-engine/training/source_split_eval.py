"""Source-separated evaluation: realistic estimate on unseen campaigns.

Splits by the `source` column when present (entire datasets/campaigns held
out); falls back to a stratified random split otherwise. Reports phishing
precision/recall/F1, false-positive/negative rates, log loss and Brier
score alongside accuracy. Run: python ai-engine/training/source_split_eval.py
"""
import os
import sys
import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, log_loss, brier_score_loss,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "trained_models", "phishing_model.pkl")
VECTORIZER_PATH = os.path.join(PROJECT_ROOT, "trained_models", "tfidf_vectorizer.pkl")


def metrics_for(y_true, y_pred, y_proba) -> dict:
    cm = confusion_matrix(y_true, y_pred, labels=["legitimate", "phishing"])
    tn, fp, fn, tp = cm.ravel()
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_phishing": round(float(precision_score(y_true, y_pred, pos_label="phishing", zero_division=0)), 4),
        "recall_phishing": round(float(recall_score(y_true, y_pred, pos_label="phishing", zero_division=0)), 4),
        "f1_phishing": round(float(f1_score(y_true, y_pred, pos_label="phishing", zero_division=0)), 4),
        "false_positive_rate": round(float(fp / (fp + tn)) if (fp + tn) else 0.0, 4),
        "false_negative_rate": round(float(fn / (fn + tp)) if (fn + tp) else 0.0, 4),
        "log_loss": round(float(log_loss((y_true == "phishing").astype(int), y_proba)), 4),
        "brier_score": round(float(brier_score_loss((y_true == "phishing").astype(int), y_proba)), 4),
        "n": int(len(y_true)),
    }


def main() -> None:
    df = pd.read_csv(DATASET_PATH)
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    phish_idx = list(model.classes_).index("phishing")

    if "source" in df.columns and df["source"].nunique() >= 3:
        # Hold out ~20% of sources (entire campaigns unseen in training).
        sources = sorted(df["source"].unique())
        n_hold = max(1, int(len(sources) * 0.2))
        hold = set(sources[:n_hold])
        test = df[df["source"].isin(hold)]
        print(f"Holding out {len(hold)} entire sources: {sorted(hold)}")
        Xt = vectorizer.transform(test["email_text"])
        pred = model.predict(Xt)
        proba = model.predict_proba(Xt)[:, phish_idx]
        print(metrics_for(test["label"], pred, proba))
    else:
        print("No source column: run train_model.py to rebuild the dataset with provenance, then re-run.")

    # Always report the conventional stratified holdout for comparison.
    from sklearn.model_selection import train_test_split
    _, X_test, _, y_test = train_test_split(
        df["email_text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    Xt = vectorizer.transform(X_test)
    print("Stratified holdout:", metrics_for(y_test, model.predict(Xt), model.predict_proba(Xt)[:, phish_idx]))


if __name__ == "__main__":
    main()
