"""Source-split safeguard tests: synthetic frames, no artifacts needed."""
import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    "source_split_eval", ROOT / "ai-engine" / "training" / "source_split_eval.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

check_binary = _mod.check_binary
enforce_group_disjointness = _mod.enforce_group_disjointness
choose_holdout = _mod.choose_holdout


def _frame(rows):
    return pd.DataFrame(rows, columns=["email_text", "label", "source", "group_id"])


def test_missing_group_id_is_unverified():
    train = pd.DataFrame({"email_text": ["a"], "label": ["phishing"], "source": ["s1"]})
    test = pd.DataFrame({"email_text": ["b"], "label": ["legitimate"], "source": ["s2"]})
    _, verified = enforce_group_disjointness(train, test)
    assert verified is False


def test_overlapping_groups_dropped_from_train():
    train = _frame([("t1", "phishing", "s1", "g1"), ("t2", "legitimate", "s1", "g2")])
    test = _frame([("e1", "phishing", "s2", "g1")])
    filtered, verified = enforce_group_disjointness(train, test)
    assert verified is True
    assert set(filtered["group_id"]).isdisjoint(set(test["group_id"]))


def test_single_class_rejected():
    one_class = _frame([("a", "phishing", "s1", "g1"), ("b", "phishing", "s1", "g2")])
    with pytest.raises(ValueError):
        check_binary(one_class, "holdout")


def test_choose_holdout_needs_both_classes():
    legit = [("ok %d" % i, "legitimate", "s-legit", "g-l%d" % i) for i in range(60)]
    phish = [("bad %d" % i, "phishing", "s-phish", "g-p%d" % i) for i in range(60)]
    df = pd.DataFrame(legit + phish, columns=["email_text", "label", "source", "group_id"])
    train_sources, hold_sources = choose_holdout(df)
    hold = df[df["source"].isin(hold_sources)]
    assert set(hold["label"].unique()) == {"legitimate", "phishing"}
    assert set(train_sources).isdisjoint(set(hold_sources))
