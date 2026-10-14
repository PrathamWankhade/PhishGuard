"""Adversarial suite calibrated to the CI FIXTURE model.

The full adversarial suite (test_adversarial.py) encodes the production
model's measured baseline. THIS module encodes the deterministic fixture
model's measured behavior (7/7 phishing -> Phishing, 0/5 legitimate ->
Phishing) so the integration CI job exercises adversarial paths too.

Skipped automatically unless trained_models/model_metadata.json carries
{"fixture": true} — i.e. runs in the fixture integration job, never against
a production model.
"""
import json
from pathlib import Path

import pytest

from backend.app.services.phishing_detector import detect_phishing

ROOT = Path(__file__).resolve().parents[1]

try:
    _fixture = bool(json.loads((ROOT / "trained_models" / "model_metadata.json").read_text()).get("fixture"))
except Exception:
    _fixture = False

pytestmark = [
    pytest.mark.model,
    pytest.mark.skipif(not _fixture, reason="fixture-model expectations only"),
]

FIXTURES = [json.loads(line) for line in
            (ROOT / "tests" / "fixtures" / "adversarial.jsonl").read_text().splitlines()]


def test_fixture_catches_all_phishing():
    missed = [c["id"] for c in FIXTURES if c["label"] == "phishing"
              and detect_phishing(c["text"], c["sender"], c.get("reply_to", ""))["verdict"] != "Phishing Email"]
    assert not missed, f"fixture missed phishing: {missed}"


def test_fixture_flags_no_legitimate_as_phishing():
    fps = [c["id"] for c in FIXTURES if c["label"] == "legitimate"
           and detect_phishing(c["text"], c["sender"], c.get("reply_to", ""))["verdict"] == "Phishing Email"]
    assert not fps, f"fixture false positives: {fps}"
