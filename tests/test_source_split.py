"""Source-split safeguard tests: synthetic frames, no artifacts needed.

The first block unit-tests the protocol's helpers. The last test runs the
whole protocol (run_eval) end-to-end on a synthetic multi-source corpus so CI
proves the wiring, not just the parts -- it asserts no quality value, because
a toy corpus says nothing about detector accuracy. Real numbers come from
running source_split_eval.py against the real dataset where the resources
allow it.
"""
import csv
import importlib.util
import json
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
run_eval = _mod.run_eval


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


# ---------------------------------------------------------------------------
# End-to-end protocol run on a synthetic corpus (no model artifacts needed).
# ---------------------------------------------------------------------------

# Each source gets its own vocabulary so a source is genuinely unseen when
# held out -- a shared vocabulary would make sources indistinguishable and the
# split meaningless.
_PHISH_SOURCES = ["src_nazario", "src_fraud", "src_trec05", "src_spam_a"]
_LEGIT_SOURCES = ["src_enron", "src_ceas", "src_easy_ham", "src_hard_ham"]
_PHISH_WORDS = ["urgent", "verify", "password", "credential", "wire", "giftcard", "suspend", "login"]
_LEGIT_WORDS = ["meeting", "invoice", "schedule", "review", "attached", "notes", "thanks", "team"]


def _text(words, seed: int) -> str:
    picked = [words[(seed * 7 + i * 3) % len(words)] for i in range(16)]
    return "please review this message " + " ".join(picked)


def _write_corpus(path: Path) -> None:
    rows, group_id = [], 0
    duplicate = None
    for label, sources, words in (
        ("phishing", _PHISH_SOURCES, _PHISH_WORDS),
        ("legitimate", _LEGIT_SOURCES, _LEGIT_WORDS),
    ):
        for source in sources:
            for n in range(60):
                text = _text(words, n)
                group_id += 1
                rows.append({
                    "email_text": text, "label": label, "source": source,
                    "sources": source, "group_id": f"g{group_id}",
                })
                # One cross-source duplicate: same text and group under a
                # different source. Breaks group disjointness only if the
                # evaluator stops dropping leaked groups.
                if duplicate is None:
                    duplicate = f"g{group_id}"
                    partner = sources[(sources.index(source) + 1) % len(sources)]
                    rows.append({
                        "email_text": text, "label": label, "source": partner,
                        "sources": f"{source}|{partner}", "group_id": duplicate,
                    })
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["email_text", "label", "source", "sources", "group_id"]
        )
        writer.writeheader()
        writer.writerows(rows)


def test_run_eval_protocol_end_to_end(tmp_path):
    pytest.importorskip("sklearn")
    dataset = tmp_path / "final_emails.csv"
    report = tmp_path / "source_split_eval.json"
    _write_corpus(dataset)

    result = run_eval(dataset_path=str(dataset), report_path=str(report))

    # The protocol only claims disjointness when it could actually verify it.
    assert result["group_disjoint"] is True

    # Whole sources are held out; none leaks across the split.
    assert set(result["train_sources"]).isdisjoint(set(result["held_out_sources"]))

    # Both classes present on both sides (protocol precondition).
    for side in (result["train_class_counts"], result["holdout_class_counts"]):
        assert {"legitimate", "phishing"} <= set(side)

    # Report contract written to the requested path, with the documented keys.
    assert report.exists()
    written = json.loads(report.read_text(encoding="utf-8"))
    assert written["held_out_sources"] == result["held_out_sources"]
    assert set(written["metrics"]) >= {
        "accuracy", "precision_phishing", "recall_phishing", "f1_phishing",
        "false_positive_rate", "false_negative_rate", "confusion_matrix",
    }
    assert written["metrics"]["n"] == sum(result["holdout_class_counts"].values())

    # Deliberately no accuracy/quality assertion: a 4-source toy corpus says
    # nothing about detector quality.
