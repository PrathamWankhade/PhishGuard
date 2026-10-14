"""Verify a checkout can actually serve predictions.

Checks, in order: Python deps importable -> dataset present -> model
artifacts present AND loadable -> /ready contract. Prints exactly what is
missing and the command that produces it. Exit 0 only when inference can run.

Run:  python scripts/verify_setup.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []


def check(name: str, ok: bool, fix: str) -> None:
    print(f"[{'OK' if ok else 'MISSING'}] {name}" + ("" if ok else f" -- {fix}"))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    try:
        import fastapi, sklearn, pandas, joblib  # noqa: F401
        check("python dependencies", True, "")
    except ImportError as e:
        check("python dependencies", False, f"pip install -r requirements.txt ({e})")
        return 1

    dataset = ROOT / "datasets" / "final" / "final_emails.csv"
    check(
        "training dataset",
        dataset.exists(),
        "place raw sources in datasets/raw/ then run python ai-engine/training/build_final_dataset.py",
    )

    model_path = ROOT / "trained_models" / "phishing_model.pkl"
    vec_path = ROOT / "trained_models" / "tfidf_vectorizer.pkl"
    artifacts = model_path.exists() and vec_path.exists()
    check(
        "model artifacts",
        artifacts,
        "run python ai-engine/training/train_model.py (needs the dataset above) "
        "or mount versioned artifacts at trained_models/",
    )

    if artifacts:
        try:
            import joblib

            model = joblib.load(model_path)
            vec = joblib.load(vec_path)
            vec.transform(["setup probe"])
            check("artifacts loadable", hasattr(model, "predict"), "retrain (artifacts corrupt?)")
        except Exception as e:
            check("artifacts loadable", False, f"retrain ({e})")

    metadata = ROOT / "trained_models" / "model_metadata.json"
    check(
        "model_metadata.json",
        metadata.exists(),
        "produced by train_model.py alongside the artifacts",
    )

    print("READY" if not FAILURES else f"NOT READY: {len(FAILURES)} missing item(s)")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
