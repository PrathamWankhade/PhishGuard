"""The policy risk formula must have exactly one implementation.

It used to live inline in scripts/validate_policy.py, which meant a change to
phishing_detector.py would silently leave the validated report describing a
formula that is no longer shipped -- the report would stay green and be wrong.

phishing_detector.compute_risk_score is now the single source of truth. These
tests fail if a consumer re-derives the formula instead of calling it.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DETECTOR = ROOT / "backend" / "app" / "services" / "phishing_detector.py"
CONSUMERS = [
    ROOT / "scripts" / "validate_policy.py",
    ROOT / "ai-engine" / "training" / "threshold_analysis.py",
]

# Fragments of the old inline copy. Any of these reappearing means someone
# re-derived the formula rather than calling the helper.
INLINE_FORMULA_MARKERS = [
    r"min\(\s*20\s*,\s*urls\.get",
    r"min\(\s*10\s*,.*auth.*bec",
    r"\*\s*100\s*\n?\s*\+",            # proba*100 + ...
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_detector_exposes_one_authoritative_formula():
    src = _read(DETECTOR)
    assert src.count("def compute_risk_score(") == 1
    # The detector must consume its own helper rather than a second copy.
    assert "risk_score = compute_risk_score(" in src, (
        "detect_phishing must call compute_risk_score, not re-derive the score"
    )


def test_no_consumer_re_derives_the_formula():
    for path in CONSUMERS:
        assert path.exists(), f"expected consumer {path}"
        src = _read(path)
        assert "compute_risk_score" in src, f"{path.name} must call compute_risk_score"
        for marker in INLINE_FORMULA_MARKERS:
            assert not re.search(marker, src), (
                f"{path.name} re-derives the policy risk formula ({marker!r}); "
                "call phishing_detector.compute_risk_score instead"
            )


def test_shipped_thresholds_match_classify_risk():
    """The constants the reports cite are the ones classify_risk actually uses."""
    import importlib.util
    import sys

    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("_pd", DETECTOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    high, medium = mod.RISK_HIGH_THRESHOLD, mod.RISK_MEDIUM_THRESHOLD
    assert medium < high, "medium threshold must sit below the high threshold"
    assert mod.classify_risk(high) == "high"
    assert mod.classify_risk(high - 0.01) == "medium"
    assert mod.classify_risk(medium) == "medium"
    assert mod.classify_risk(medium - 0.01) == "low"