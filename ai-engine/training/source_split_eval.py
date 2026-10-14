"""Source-separated evaluation WITHOUT leakage.

Protocol (in this order):
  1. Split SOURCES first (entire campaigns held out, reproducibly).
  2. Train a FRESH Pipeline(TFIDF -> ensemble) on train sources ONLY.
  3. Evaluate ONLY on held-out sources the model never saw.

This measures generalization to unseen campaigns. Never evaluate a model on
rows it trained on and call it source-separated.

Run:  python ai-engine/training/source_split_eval.py
"""
import json
import os

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, brier_score_loss, confusion_matrix, f1_score, log_loss,
    precision_score, recall_score,
)
from sklearn.pipeline import Pipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv")
REPORT_PATH = os.path.join(PROJECT_ROOT, "reports", "source_split_eval.json")

HOLDOUT_FRAC = 0.2
SOURCE_SEED = 7
MIN_HOLDOUT_PER_CLASS = 50


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
        "confusion_matrix": cm.tolist(),
        "n": int(len(y_true)),
    }


def choose_holdout(df: pd.DataFrame) -> tuple[list, list]:
    """Reproducibly hold out whole sources (seeded shuffle, then accumulate
    to HOLDOUT_FRAC), requiring >= MIN_HOLDOUT_PER_CLASS of each class in the
    holdout. Deterministic given SOURCE_SEED — recorded in the report."""
    import random

    counts = df["source"].value_counts()
    order = sorted(counts.index)
    random.Random(SOURCE_SEED).shuffle(order)
    hold, n_hold = [], 0
    target = int(len(df) * HOLDOUT_FRAC)
    for source in order:
        if n_hold >= target:
            break
        hold.append(source)
        n_hold += int(counts[source])
    labels = df[df["source"].isin(hold)]["label"].value_counts()
    for source in order:
        if source in hold:
            continue
        if labels.get("legitimate", 0) >= MIN_HOLDOUT_PER_CLASS and labels.get("phishing", 0) >= MIN_HOLDOUT_PER_CLASS:
            break
        hold.append(source)
        labels = df[df["source"].isin(hold)]["label"].value_counts()
    if labels.get("legitimate", 0) < MIN_HOLDOUT_PER_CLASS or labels.get("phishing", 0) < MIN_HOLDOUT_PER_CLASS:
        raise ValueError(f"Holdout lacks sufficient classes: {labels.to_dict()}")
    train = sorted(set(df["source"].unique()) - set(hold))
    return train, sorted(hold)


def enforce_group_disjointness(train_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Drop train rows whose duplicate-group also appears in the holdout.

    Returns (filtered_train, verified). verified is False when the check was
    impossible (no group_id column) — callers must NOT report success then.
    """
    if "group_id" not in train_df.columns or "group_id" not in test_df.columns:
        return train_df, False
    leaked = set(train_df["group_id"]) & set(test_df["group_id"])
    if leaked:
        print(f"Dropping {len(leaked)} duplicate groups from train (present in holdout).")
        train_df = train_df[~train_df["group_id"].isin(leaked)]
    return train_df, True


def check_binary(df: pd.DataFrame, name: str) -> None:
    labels = set(df["label"].unique())
    if labels != {"legitimate", "phishing"}:
        raise ValueError(f"{name} lacks both classes: {sorted(labels)} (n={len(df)})")


def main() -> None:
    df = pd.read_csv(DATASET_PATH)
    if "source" not in df.columns:
        raise SystemExit(
            "Dataset has no 'source' column. Rebuild with "
            "ai-engine/training/build_final_dataset.py first."
        )
    train_sources, hold_sources = choose_holdout(df)
    print(f"Train sources ({len(train_sources)}): {train_sources}")
    print(f"Held-out sources ({len(hold_sources)}): {hold_sources}")

    train_df = df[df["source"].isin(train_sources)]
    test_df = df[df["source"].isin(hold_sources)]
    train_df, group_verified = enforce_group_disjointness(train_df, test_df)
    if not group_verified:
        raise SystemExit(
            "INCONCLUSIVE: no group_id column — duplicate-group separation "
            "cannot be verified. Rebuild the dataset with build_final_dataset.py."
        )
    check_binary(train_df, "train set")
    check_binary(test_df, "holdout set")
    assert set(train_df["group_id"]).isdisjoint(set(test_df["group_id"])), \
        "group leakage: train and holdout share duplicate groups"
    print(f"Train rows: {len(train_df)}, held-out rows: {len(test_df)}")
    print(f"Train class balance: {train_df['label'].value_counts().to_dict()}")
    print(f"Holdout class balance: {test_df['label'].value_counts().to_dict()}")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            stop_words="english", max_features=50000,
            ngram_range=(1, 3), sublinear_tf=True,
        )),
        ("clf", VotingClassifier(
            estimators=[
                ("lr", LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42, C=1.0)),
                ("rf", RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)),
            ],
            voting="soft",
        )),
    ])
    pipeline.fit(train_df["email_text"], train_df["label"])

    proba = pipeline.predict_proba(test_df["email_text"])[
        :, list(pipeline.classes_).index("phishing")
    ]
    report = {
        "holdout_strategy": f"seeded group split (seed={SOURCE_SEED}, frac={HOLDOUT_FRAC})",
        "train_sources": train_sources,
        "held_out_sources": hold_sources,
        "train_class_counts": {k: int(v) for k, v in train_df["label"].value_counts().items()},
        "holdout_class_counts": {k: int(v) for k, v in test_df["label"].value_counts().items()},
        "group_disjoint": bool(group_verified),
        "note": "Holdout is untouched by threshold selection; re-validate policy thresholds here, do not tune them here.",
        "metrics": metrics_for(test_df["label"], pipeline.predict(test_df["email_text"]), proba),
    }
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    print(f"Saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
