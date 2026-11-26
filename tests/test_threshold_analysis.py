"""Threshold-analysis math and contract tests.

These exercise the sweep/selection functions on synthetic arrays: they need no
model artifacts and no dataset, so CI can prove the math the same way it proves
the source-split protocol. The real sweep (reports/threshold_analysis.json)
comes from running ai-engine/training/threshold_analysis.py where trained_models/
exists.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "threshold_analysis", ROOT / "ai-engine" / "training" / "threshold_analysis.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

evaluate_thresholds = _mod.evaluate_thresholds
select_threshold = _mod.select_threshold
to_binary = _mod.to_binary


# A small separating population: phishing gets high scores, legitimate low, with
# an overlap band so no threshold is perfect and the sweep has real trade-offs.
Y = np.array([1] * 60 + [0] * 60)
P = np.concatenate([
    np.linspace(0.85, 1.0, 30),   # clearly phishing
    np.linspace(0.40, 0.70, 30),  # borderline phishing (some lost below 0.7)
    np.linspace(0.05, 0.45, 50),  # mostly legitimate
    np.linspace(0.50, 0.75, 10),  # borderline legit mistaken for phishing
])


def test_to_binary_accepts_all_label_forms():
    assert list(to_binary(["phishing", "legitimate"])) == [1, 0]
    assert list(to_binary(["Phishing", "Safe"])) == [1, 0]
    assert list(to_binary(np.array([1, 0], dtype=bool))) == [1, 0]
    assert list(to_binary(["spam", "ham"])) == [1, 0]


def test_to_binary_rejects_unknown_labels():
    with pytest.raises(ValueError):
        to_binary(["phishing", "maybe"])


def test_confusion_counts_partition_the_population():
    rows = evaluate_thresholds(Y, P, thresholds=[0.5])
    r = rows[0]
    assert r["tp"] + r["fp"] + r["tn"] + r["fn"] == len(Y)
    assert r["n"] == len(Y)


def test_zero_division_guards_report_zero_not_crash():
    """A threshold above every score has no positive predictions.

    The roadmap's original snippet divided by (tp + fp) unguarded and used
    average='binary' on string labels; both raise instead of reporting.
    """
    rows = evaluate_thresholds(Y, P, thresholds=[2.0])
    r = rows[0]
    assert r["tp"] == 0 and r["fp"] == 0
    assert r["precision"] == 0.0, "precision with no positive predictions must be 0.0, not 1.0 or ZeroDivisionError"
    assert r["recall"] == 0.0
    assert r["flagged"] == 0.0


def test_monotonicity_of_threshold_sweep():
    """Raising the threshold can only lower recall and flagged rate."""
    rows = evaluate_thresholds(Y, P, thresholds=[0.2, 0.5, 0.8])
    recall = [r["recall"] for r in rows]
    flagged = [r["flagged"] for r in rows]
    assert recall == sorted(recall, reverse=True)
    assert flagged == sorted(flagged, reverse=True)


def test_select_threshold_target_recall_is_lowest_qualifying():
    best = select_threshold(Y, P, target_recall=0.9, thresholds=np.arange(0.05, 1.01, 0.05))
    assert best["attainable"] is True
    assert best["recall"] >= 0.9
    # Lowest threshold that still clears the floor -> keeps the most precision.
    qualifying = [
        r for r in evaluate_thresholds(Y, P, thresholds=np.arange(0.05, 1.01, 0.05))
        if r["recall"] >= 0.9
    ]
    assert best["threshold"] == min(r["threshold"] for r in qualifying)


def test_select_threshold_unattainable_recall_is_reported_not_faked():
    # recall > 1.0 is mathematically unreachable, so no threshold can qualify.
    best = select_threshold(Y, P, target_recall=1.5)
    assert best["attainable"] is False
    assert "no threshold reaches recall" in best["detail"]


def test_select_threshold_min_precision_is_highest_qualifying():
    best = select_threshold(Y, P, min_precision=0.9, thresholds=np.arange(0.05, 1.01, 0.05))
    assert best["attainable"] is True
    assert best["precision"] >= 0.9


def test_select_threshold_defaults_to_max_f1():
    best = select_threshold(Y, P, thresholds=np.arange(0.05, 1.01, 0.05))
    assert best["objective"] == "max_f1"
    assert best["f1"] == max(r["f1"] for r in evaluate_thresholds(Y, P, thresholds=np.arange(0.05, 1.01, 0.05)))