import csv, os, re, sys, random, email, shutil, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
from html import unescape
from collections import defaultdict

csv.field_size_limit(2**31 - 1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "datasets" / "raw"
FINAL_DIR = PROJECT_ROOT / "datasets" / "final"
FINAL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = FINAL_DIR / "final_emails.csv"

LABELED_FILES = [
    "CEAS_08.csv", "Enron.csv", "Ling.csv", "Nazario.csv",
    "Nazario_5.csv", "Nigerian_5.csv", "Nigerian_Fraud.csv",
    "SpamAssasin.csv", "TREC_05.csv", "TREC_06.csv", "TREC_07.csv",
]

MAILDIR_BASE = "spamassassin"
MAILDIRS = {
    "20021010_easy_ham":   "legitimate",
    "20030228_easy_ham":   "legitimate",
    "20030228_easy_ham_2": "legitimate",
    "20030228_hard_ham":   "legitimate",
    "20021010_spam":       "phishing",
    "20030228_spam":       "phishing",
    "20030228_spam_2":     "phishing",
    "20050311_spam_2":     "phishing",
}

def clean_text(text):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9:/@._\-\s]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()

def combine(subject, body):
    parts = []
    if subject:
        parts.append(clean_text(subject))
    if body:
        parts.append(clean_text(body))
    return re.sub(r"\s+", " ", " ".join(parts)).strip()

def parse_raw_email(msg_text):
    subject = ""
    body = ""
    try:
        msg = email.message_from_string(msg_text)
        subject = msg.get("Subject", "")
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    if isinstance(body, bytes):
                        body = body.decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True)
            if isinstance(body, bytes):
                body = body.decode("utf-8", errors="ignore")
    except Exception:
        lines = msg_text.split("\n")
        body_lines = []
        in_headers = True
        for line in lines:
            if in_headers:
                if line.lower().startswith("subject:"):
                    subject = line[8:].strip()
                if line.strip() == "":
                    in_headers = False
            else:
                body_lines.append(line)
        body = "\n".join(body_lines)
    return subject, body

# ============================================================
# PROCESS LABELED CSVs
# ============================================================

def process_labeled_csvs():
    print("=" * 60)
    print("  LABELED CSV FILES")
    print("=" * 60)

    all_rows = []
    grand = {"legitimate": 0, "phishing": 0}

    for fname in LABELED_FILES:
        path = os.path.join(str(RAW_DIR), fname)
        if not os.path.exists(path):
            print(f"  SKIP  {fname}")
            continue

        rows = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            has_subject = "subject" in reader.fieldnames
            for row in reader:
                lbl = (row.get("label") or "").strip().lower()
                if lbl not in ("0", "1"):
                    continue
                text = combine(row.get("subject"), row.get("body")) if has_subject else clean_text(row.get("body", ""))
                if len(text) < 20:
                    continue
                label = "legitimate" if lbl == "0" else "phishing"
                rows.append({"email_text": text, "label": label, "source": fname})

        c_legit = sum(1 for r in rows if r["label"] == "legitimate")
        c_phish = sum(1 for r in rows if r["label"] == "phishing")
        avg_len = int(sum(len(r["email_text"]) for r in rows) / len(rows)) if rows else 0
        pct_phish = c_phish / (c_legit + c_phish) * 100 if (c_legit + c_phish) else 0

        print(f"  {fname:20s}  {len(rows):>6} rows  ({c_legit:>5} legit, {c_phish:>5} phish)  "
              f"avg {avg_len:>5} chars  {pct_phish:5.1f}% phish")

        all_rows.extend(rows)
        grand["legitimate"] += c_legit
        grand["phishing"] += c_phish

    return all_rows, grand

# ============================================================
# PROCESS SPAMASSASSIN MAILDIRS
# ============================================================

def process_maildirs():
    print("\n" + "=" * 60)
    print("  SPAMASSASSIN MAILDIRS")
    print("=" * 60)

    all_rows = []
    grand = {"legitimate": 0, "phishing": 0}
    base = os.path.join(str(RAW_DIR), MAILDIR_BASE)

    for dirname, label in MAILDIRS.items():
        dir_path = os.path.join(base, dirname)
        if not os.path.isdir(dir_path):
            print(f"  SKIP  {dirname} (not found)")
            continue

        items = os.listdir(dir_path)
        subdirs = [d for d in items if os.path.isdir(os.path.join(dir_path, d))]
        file_dir = os.path.join(dir_path, subdirs[0]) if subdirs else dir_path
        files = [f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(file_dir, f))]

        rows = []
        for fname in files:
            try:
                with open(os.path.join(file_dir, fname), "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                subject, body = parse_raw_email(raw)
                text = combine(subject, body)
                if len(text) >= 20:
                    rows.append({"email_text": text, "label": label, "source": f"maildir:{dirname}"})
            except Exception:
                pass

        avg_len = int(sum(len(r["email_text"]) for r in rows) / len(rows)) if rows else 0
        print(f"  {dirname:20s}  {len(rows):>6} rows  ({len(files):>5} files)  "
              f"avg {avg_len:>5} chars  label={label}")

        all_rows.extend(rows)
        grand[label] += len(rows)

    return all_rows, grand

# ============================================================
# MAIN
# ============================================================


# ============================================================
# MAIN
# ============================================================

def build_dataset(output_path: str | None = None) -> dict:
    """Build the final dataset, writing columns:

        email_text, label, source, sources, group_id

    `source` is the primary contributing source, `sources` every source the
    (deduplicated) text came from, and `group_id` a stable duplicate-group key
    so related records can be held disjoint across train/test splits.

    Non-destructive: when the destination already exists a timestamped backup
    is made first, and a warning is printed. The produced dataset and the
    dumped artifacts in trained_models/ are a MATCHED PAIR -- rebuilding one
    silently invalidates every metric reported for the other, because
    train_model.py / evaluate_model.py split on a fixed seed against the
    dataset that was current at training time. Always re-run train_model.py
    and then evaluate_model.py after rebuilding.
    """
    out_path = os.path.realpath(output_path or str(OUTPUT))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if os.path.exists(out_path):
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        backup = f"{out_path}.{stamp}.bak"
        shutil.copy2(out_path, backup)
        print(f"  WARNING: {os.path.basename(out_path)} already exists; backup at {backup}")
        print("  WARNING: rebuilt dataset no longer matches dumped model artifacts.")
        print("           Re-run ai-engine/training/train_model.py, then")
        print("           ai-engine/training/evaluate_model.py, before trusting metrics.")

    print("BUILD FINAL DATASET  v2")
    print("=" * 60)
    print()

    csv_rows, csv_counts = process_labeled_csvs()
    mail_rows, mail_counts = process_maildirs()

    all_rows = csv_rows + mail_rows
    print("\n" + "=" * 60)
    print("  MERGE")
    print("=" * 60)
    print(f"  Labeled CSVs:          {len(csv_rows):>7} rows")
    print(f"  SpamAssassin maildirs: {len(mail_rows):>7} rows")
    print(f"  TOTAL:                 {len(all_rows):>7} rows")
    print(f"  Legitimate:            {csv_counts['legitimate'] + mail_counts['legitimate']:>7}")
    print(f"  Phishing:              {csv_counts['phishing'] + mail_counts['phishing']:>7}")

    print("\n  Deduplicating...")

    def canonical_key(text: str) -> str:
        normalized = re.sub(r"\s+", " ", (text or "").strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    seen: dict[str, int] = {}
    deduped = []
    conflicts = 0
    for r in all_rows:
        key = canonical_key(r["email_text"])
        if key not in seen:
            seen[key] = len(deduped)
            r["sources"] = r.get("source", "")
            deduped.append(r)
        else:
            # Same normalized text seen before: merge provenance, keep first.
            first = deduped[seen[key]]
            src = r.get("source", "")
            prior = first.get("sources", "").split("|") if first.get("sources") else []
            if src and src not in prior:
                prior.append(src)
                first["sources"] = "|".join(prior)
            if first["label"] != r["label"]:
                conflicts += 1
    print(f"  Label conflicts on duplicate text: {conflicts} (first occurrence kept)")

    print(f"  After dedup: {len(deduped)} rows (removed {len(all_rows) - len(deduped)})")
    random.seed(42)
    random.shuffle(deduped)

    c_legit = sum(1 for r in deduped if r["label"] == "legitimate")
    c_phish = sum(1 for r in deduped if r["label"] == "phishing")
    total = len(deduped)
    pct_legit = c_legit / total * 100 if total else 0.0
    pct_phish = c_phish / total * 100 if total else 0.0
    print(f"  Legitimate: {c_legit}  ({pct_legit:.1f}%)")
    print(f"  Phishing:   {c_phish}  ({pct_phish:.1f}%)")
    if total == 0:
        raise SystemExit(
            "No rows survived cleaning: check that datasets/raw is populated "
            "and that cleaner thresholds are not discarding every email."
        )

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email_text", "label", "source", "sources", "group_id"])
        writer.writeheader()
        for r in deduped:
            writer.writerow({
                "email_text": r["email_text"],
                "label": r["label"],
                "source": r.get("source", ""),
                # All contributing sources for this normalized text (pipe-joined),
                # plus a stable duplicate-group id so related records can be kept
                # disjoint across train/test splits.
                "sources": r.get("sources", r.get("source", "")),
                "group_id": canonical_key(r["email_text"]),
            })

    # Provenance manifest alongside the dataset.
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": len(deduped),
        "legitimate": c_legit,
        "phishing": c_phish,
        "dedup": "sha256 of normalized full text",
        "conflicting_labels": conflicts,
        "sources": sorted({r.get("source", "") for r in deduped}),
    }
    manifest_path = os.path.join(os.path.dirname(out_path), "dataset_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    size_mb = os.path.getsize(out_path) / (1024**2)
    print(f"\n  Saved: {out_path}  ({size_mb:.1f} MB)")
    print(f"  Manifest: {manifest_path}")
    print("  DONE.")
    return manifest


def main() -> None:
    build_dataset()


if __name__ == "__main__":
    main()
