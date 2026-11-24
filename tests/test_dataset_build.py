"""Dataset-build guardrails: provenance columns and non-destructive writes.

`build_final_dataset.py` aggregates 11 labelled CSVs plus 8 SpamAssassin
maildirs (about 1.8 GB of raw input). These tests monkeypatch the two loaders
so the file-writing half of the build is exercised in seconds, without
touching datasets/final or reading the raw corpus.
"""
import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "build_final_dataset", ROOT / "ai-engine" / "training" / "build_final_dataset.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# A corpus with a deliberate cross-source duplicate so the dedup/provenance
# merge path in build_dataset actually runs.
_STUB_ROWS = [
    {"email_text": "urgent verify your password now", "label": "phishing", "source": "src_a"},
    {"email_text": "please review the meeting notes", "label": "legitimate", "source": "src_b"},
    # Same normalized text as row 1 but from another source: must merge into
    # one row whose `sources` lists both, keeping the first label.
    {"email_text": "urgent verify your password now", "label": "phishing", "source": "src_c"},
    # Conflicting label on duplicate text: first occurrence wins, conflict is
    # counted and surfaced in the manifest.
    {"email_text": "urgent verify your password now", "label": "legitimate", "source": "src_d"},
]
_STUB_COUNTS = {"legitimate": 2, "phishing": 2}


def _stub_loaders(monkeypatch):
    monkeypatch.setattr(
        _mod, "process_labeled_csvs", lambda: (list(_STUB_ROWS), dict(_STUB_COUNTS))
    )
    monkeypatch.setattr(_mod, "process_maildirs", lambda: ([], {"legitimate": 0, "phishing": 0}))


def test_existing_dataset_is_backed_up_not_clobbered(tmp_path, monkeypatch):
    _stub_loaders(monkeypatch)

    out = tmp_path / "final_emails.csv"
    original = "email_text,label\n"
    out.write_text(original, encoding="utf-8")

    _mod.build_dataset(output_path=str(out))

    backups = list(tmp_path.glob("final_emails.csv.*.bak"))
    assert backups, "an existing dataset was overwritten in place instead of backed up"
    assert backups[0].read_text(encoding="utf-8") == original, "backup is not the original content"


def test_written_dataset_carries_provenance_columns(tmp_path, monkeypatch):
    _stub_loaders(monkeypatch)

    out = tmp_path / "final_emails.csv"
    manifest = _mod.build_dataset(output_path=str(out))

    with open(out, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert list(rows[0].keys()) == [
        "email_text", "label", "source", "sources", "group_id",
    ], "dataset must carry source and duplicate-group provenance"

    # Cross-source duplicates collapse to one row that records every source.
    assert len(rows) == 2, "duplicate full-text records should merge into one row"
    merged = [r for r in rows if "urgent verify" in r["email_text"]]
    assert len(merged) == 1
    # Every contributing source is recorded in `sources`, including src_d whose
    # duplicate carried a conflicting label.
    assert set(merged[0]["sources"].split("|")) == {"src_a", "src_c", "src_d"}
    assert merged[0]["label"] == "phishing", "first occurrence's label must win"
    assert all(r["group_id"] for r in rows), "every row needs a group_id"

    manifest_path = tmp_path / "dataset_manifest.json"
    assert manifest_path.exists(), "provenance manifest was not written alongside the dataset"
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written == manifest
    assert written["rows"] == len(rows)
    assert written["conflicting_labels"] == 1, "label conflict on duplicate text must be reported"
    assert "created_at" in written and "dedup" in written