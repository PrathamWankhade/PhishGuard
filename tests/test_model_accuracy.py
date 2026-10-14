import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai-engine"))

from training.evaluate_model import evaluate_model

pytestmark = pytest.mark.model


def test_model_accuracy_threshold():
    metrics = evaluate_model()
    assert metrics["accuracy"] >= 0.90, f"Model accuracy {metrics['accuracy']} is below 0.90"
    assert metrics["precision"] >= 0.85, f"Precision {metrics['precision']} is below 0.85"
    assert metrics["recall"] >= 0.85, f"Recall {metrics['recall']} is below 0.85"
    assert metrics["f1"] >= 0.85, f"F1 {metrics['f1']} is below 0.85"
