import os
import hashlib
import joblib
import json
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_score, recall_score, f1_score, log_loss, brier_score_loss,
)
from sklearn.pipeline import Pipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "trained_models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "phishing_model.pkl")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")

print("Loading dataset...")
dataset = pd.read_csv(DATASET_PATH)
print(f"Total emails: {len(dataset)}")
print(dataset["label"].value_counts())

X = dataset["email_text"]
y = dataset["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Vectorizing text with n-grams (1,3)...")
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=50000,
    ngram_range=(1, 3),
    sublinear_tf=True,
)

lr = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42, C=1.0)
rf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1)

ensemble = VotingClassifier(
    estimators=[("lr", lr), ("rf", rf)],
    voting="soft",
)

# Fit vectorizer + model on the training split for the released artifact.
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)
print("Training ensemble model (LogisticRegression + RandomForest)...")
ensemble.fit(X_train_tfidf, y_train)

print("Performing 5-fold cross-validation (pipeline: TF-IDF inside each fold)...")
cv_pipeline = Pipeline([
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
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(cv_pipeline, X_train, y_train, cv=cv, scoring="f1_macro")
print(f"Cross-validation F1-macro: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 2:.2f})")

predictions = ensemble.predict(X_test_tfidf)
proba = ensemble.predict_proba(X_test_tfidf)
accuracy = accuracy_score(y_test, predictions)

print(f"\nTest Accuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, predictions))

cm = confusion_matrix(y_test, predictions)
print(f"Confusion Matrix:\n{cm}")

# Phishing-class operational metrics + calibration (required before showing %).
y_binary = (y_test == "phishing").astype(int)
phish_proba = proba[:, list(ensemble.classes_).index("phishing")]
print(f"Phishing precision: {precision_score(y_test, predictions, pos_label='phishing'):.4f}")
print(f"Phishing recall:    {recall_score(y_test, predictions, pos_label='phishing'):.4f}")
print(f"Phishing F1:        {f1_score(y_test, predictions, pos_label='phishing'):.4f}")
print(f"Log loss:           {log_loss(y_binary, phish_proba):.4f}")
print(f"Brier score:        {brier_score_loss(y_binary, phish_proba):.4f}")

joblib.dump(ensemble, MODEL_PATH)
joblib.dump(vectorizer, VECTORIZER_PATH)

# Reproducibility metadata for the released artifact.
import sklearn
metadata = {
    "model_type": "soft-voting LogisticRegression + RandomForest",
    "tfidf": {"max_features": 50000, "ngram_range": [1, 3], "sublinear_tf": True, "stop_words": "english"},
    "split": {"test_size": 0.2, "random_state": 42, "stratify": True},
    "cv": {"n_splits": 5, "scoring": "f1_macro", "mean": float(cv_scores.mean()), "std": float(cv_scores.std())},
    "test": {
        "accuracy": float(accuracy),
        "precision_phishing": float(precision_score(y_test, predictions, pos_label="phishing")),
        "recall_phishing": float(recall_score(y_test, predictions, pos_label="phishing")),
        "f1_phishing": float(f1_score(y_test, predictions, pos_label="phishing")),
        "confusion_matrix": cm.tolist(),
    },
    "sklearn_version": sklearn.__version__,
    "dataset_rows": len(dataset),
}
with open(os.path.join(MODEL_DIR, "model_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
# SHA-256 of artifacts for deployment verification.
for path in (MODEL_PATH, VECTORIZER_PATH):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"SHA256({os.path.basename(path)}): {h}")

print(f"\nModel saved to {MODEL_PATH}")
print(f"Vectorizer saved to {VECTORIZER_PATH}")
