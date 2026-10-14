"""Retention enforcement for scan history.

Default policy (see docs/database_design.md): scan_history rows older than
90 days are deleted; feedback rows are kept 365 days for trend monitoring.
Always run with --dry-run first.

Usage:
  python scripts/purge_history.py --dry-run
  python scripts/purge_history.py --older-than 90 [--apply]
"""
import argparse
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

parser = argparse.ArgumentParser()
parser.add_argument("--db", default=str(ROOT / "phishing_detection.db"))
parser.add_argument("--older-than", type=int, default=90, help="scan_history age in days")
parser.add_argument("--feedback-days", type=int, default=365)
parser.add_argument("--apply", action="store_true", help="delete; without it, dry-run only")
args = parser.parse_args()

conn = sqlite3.connect(args.db)
for table, days in (("scan_history", args.older_than), ("scan_feedback", args.feedback_days)):
    try:
        n = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        ).fetchone()[0]
    except sqlite3.OperationalError as e:
        print(f"{table}: skipped ({e})")
        continue
    print(f"{table}: {n} row(s) older than {days} days" + ("" if args.apply else " [dry-run]"))
    if args.apply and n:
        conn.execute(
            f"DELETE FROM {table} WHERE created_at < datetime('now', ?)",
            (f"-{days} days",),
        )
if args.apply:
    conn.commit()
    print("Purge applied.")
conn.close()
