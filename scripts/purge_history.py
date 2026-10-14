"""Retention enforcement for scan history.

Default policy (see docs/database_design.md): scan_history rows older than
90 days are deleted; feedback rows are kept 365 days for trend monitoring.

Database resolution: --db if given, else the DATABASE_PATH environment
variable, else the repository's phishing_detection.db. The script NEVER
creates a database: it refuses to run when the file does not exist.

Usage:
  python scripts/purge_history.py --dry-run
  python scripts/purge_history.py --older-than 90 --apply
"""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_db(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("DATABASE_PATH")
    if env:
        return Path(env)
    return ROOT / "phishing_detection.db"


def purge(db_path: Path, older_than: int, feedback_days: int, dry_run: bool) -> dict:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found: {db_path}. Refusing to create one during a purge; "
            "check DATABASE_PATH or --db."
        )
    conn = sqlite3.connect(db_path)
    result = {}
    for table, days in (("scan_history", older_than), ("scan_feedback", feedback_days)):
        try:
            n = conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            ).fetchone()[0]
        except sqlite3.OperationalError as e:
            print(f"{table}: skipped ({e})")
            result[table] = 0
            continue
        print(f"{table}: {n} row(s) older than {days} days" + (" [dry-run]" if dry_run else ""))
        if not dry_run and n:
            conn.execute(
                f"DELETE FROM {table} WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
        result[table] = n
    if not dry_run:
        conn.commit()
        print("Purge applied.")
    conn.close()
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=None)
    parser.add_argument("--older-than", type=int, default=90)
    parser.add_argument("--feedback-days", type=int, default=365)
    parser.add_argument("--apply", action="store_true", help="delete; without it, dry-run only")
    parser.add_argument("--dry-run", action="store_true", help="preview only (default behavior)")
    args = parser.parse_args(argv)
    if args.apply and args.dry_run:
        print("error: --apply and --dry-run are mutually exclusive", file=sys.stderr)
        return 2
    try:
        purge(resolve_db(args.db), args.older_than, args.feedback_days, dry_run=not args.apply)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
