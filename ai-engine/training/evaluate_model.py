import os
import joblib
import pandas as pd
import json

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report, log_loss, brier_score_loss

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "final", "final_emails.csv")
MODEL_PATH = os.path.join(PROJECT_ROOT, "trained_models", "phishing_model.pkl")
VECTORIZER_PATH = os.path.join(PROJECT_ROOT, "trained_models", "tfidf_vectorizer.pkl")


def evaluate_model() -> dict:
    dataset = pd.read_csv(DATASET_PATH)
    X = dataset["email_text"]
    y = dataset["label"]

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)

    X_test_tfidf = vectorizer.transform(X_test)
    predictions = model.predict(X_test_tfidf)
    proba = model.predict_proba(X_test_tfidf)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, pos_label="phishing")
    recall = recall_score(y_test, predictions, pos_label="phishing")
    f1 = f1_score(y_test, predictions, pos_label="phishing")

    y_binary = (y_test == "phishing").astype(int)
    phish_proba = proba[:, list(model.classes_).index("phishing")]

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
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }

    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    evaluate_model()
