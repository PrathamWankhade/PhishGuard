"""Adversarial + difficult-negative evaluation (tests/fixtures/adversarial.jsonl).

Measured baseline (2026-10-23, phase4 model, body-only classifier input):
7/7 phishing caught (none classified Safe), 2/5 legitimate-but-suspicious
mails over-flagged as Phishing. This test locks those numbers as a CEILING
(do not regress), not a quality bar — the false-positive gap on legitimate
mail with suspicious words is tracked work.
"""
import json
from pathlib import Path

import pytest

from backend.app.services.phishing_detector import detect_phishing

pytestmark = pytest.mark.model

FIXTURES = [json.loads(line) for line in
            Path(__file__).parent.joinpath("fixtures", "adversarial.jsonl").read_text().splitlines()]

REQUIRED_FIELDS = ("label", "verdict", "model_prediction", "phishing_probability",
                   "risk_score", "risk_level", "signals")


def test_phishing_fixtures_all_caught():
    missed = []
    for case in FIXTURES:
        if case["label"] != "phishing":
            continue
        out = detect_phishing(case["text"], case["sender"], case.get("reply_to", ""))
        for field in REQUIRED_FIELDS:
            assert field in out
        if out["verdict"] == "Safe Email":
            missed.append(case["id"])
    assert not missed, f"phishing fixtures missed: {missed}"


def test_legitimate_false_positive_ceiling():
    fps = []
    for case in FIXTURES:
        if case["label"] != "legitimate":
            continue
        out = detect_phishing(case["text"], case["sender"], case.get("reply_to", ""))
        if out["verdict"] == "Phishing Email":
            fps.append(case["id"])
    assert len(fps) <= 2, f"false-positive regression (baseline 2/5): {fps}"
