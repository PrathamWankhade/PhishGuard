"""Retention purge tests: temp database, preview + deletion, no-accident rules."""
import sqlite3

from scripts.purge_history import purge, resolve_db


def _make_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE scan_history (id INTEGER PRIMARY KEY, created_at TIMESTAMP)")
    conn.execute("CREATE TABLE scan_feedback (id INTEGER PRIMARY KEY, created_at TIMESTAMP)")
    conn.execute("INSERT INTO scan_history (created_at) VALUES (datetime('now', '-100 days'))")
    conn.execute("INSERT INTO scan_history (created_at) VALUES (datetime('now', '-1 day'))")
    conn.execute("INSERT INTO scan_feedback (created_at) VALUES (datetime('now', '-400 days'))")
    conn.commit()
    conn.close()


def test_purge_dry_run_deletes_nothing(tmp_path):
    db = tmp_path / "t.db"
    _make_db(db)
    result = purge(db, 90, 365, dry_run=True)
    assert result == {"scan_history": 1, "scan_feedback": 1}
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0] == 2
    conn.close()


def test_purge_apply_deletes_only_old(tmp_path):
    db = tmp_path / "t.db"
    _make_db(db)
    purge(db, 90, 365, dry_run=False)
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM scan_feedback").fetchone()[0] == 0
    conn.close()


def test_purge_refuses_missing_database(tmp_path):
    import pytest

    with pytest.raises(FileNotFoundError):
        purge(tmp_path / "nope.db", 90, 365, dry_run=True)


def test_resolve_db_prefers_env(monkeypatch, tmp_path):
    import os

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "env.db"))
    assert resolve_db(None) == tmp_path / "env.db"
    assert resolve_db(str(tmp_path / "explicit.db")) == tmp_path / "explicit.db"
    del os.environ["DATABASE_PATH"]
    assert resolve_db(None).name == "phishing_detection.db"
