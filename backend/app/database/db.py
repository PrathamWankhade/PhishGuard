import os
import sqlite3

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

DB_NAME = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "phishing_detection.db"))
_db_initialized = False


def get_connection():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scan_history'"
    )
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute(
            """
            CREATE TABLE scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner TEXT NOT NULL DEFAULT 'anonymous',
                email_hash TEXT NOT NULL,
                sender TEXT,
                email_text TEXT,
                prediction TEXT,
                confidence REAL,
                risk_level TEXT,
                reasons TEXT,
                scan_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner, email_hash)
            )
            """
        )
    else:
        cursor.execute("PRAGMA table_info(scan_history)")
        cols = {row[1] for row in cursor.fetchall()}
        if "owner" not in cols:
            cursor.execute(
                "ALTER TABLE scan_history ADD COLUMN owner TEXT NOT NULL DEFAULT 'anonymous'"
            )
            cursor.execute(
                "UPDATE scan_history SET owner='anonymous' WHERE owner IS NULL OR owner=''"
            )

        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='scan_history'"
        )
        row = cursor.fetchone()
        create_sql = (row[0] if row else "") or ""
        if "UNIQUE(owner" not in create_sql and "email_hash TEXT UNIQUE" in create_sql:
            cursor.execute(
                """
                CREATE TABLE scan_history_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner TEXT NOT NULL DEFAULT 'anonymous',
                    email_hash TEXT NOT NULL,
                    sender TEXT,
                    email_text TEXT,
                    prediction TEXT,
                    confidence REAL,
                    risk_level TEXT,
                    reasons TEXT,
                    scan_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(owner, email_hash)
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO scan_history_new
                    (id, owner, email_hash, sender, email_text, prediction, confidence, risk_level, reasons, scan_count, created_at)
                SELECT id, COALESCE(NULLIF(owner, ''), 'anonymous'), email_hash, sender, email_text, prediction, confidence, risk_level, reasons, scan_count, created_at
                FROM scan_history
                """
            )
            cursor.execute("DROP TABLE scan_history")
            cursor.execute("ALTER TABLE scan_history_new RENAME TO scan_history")

    cursor.execute("PRAGMA table_info(scan_history)")
    cols = {row[1] for row in cursor.fetchall()}
    if "reasons" not in cols:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN reasons TEXT")
    if "scan_count" not in cols:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN scan_count INTEGER DEFAULT 1")
    conn.commit()
    conn.close()
