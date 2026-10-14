"""Analyst feedback loop.

Reviewed labels are stored separately from scan history and are NEVER
treated as verified training data without human review. Used to monitor
false-positive / false-negative rates over time.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.app.database.db import get_connection
from backend.app.middleware.auth import require_api_key

router = APIRouter()


class FeedbackIn(BaseModel):
    email_hash: str
    verdict_correct: bool
    true_label: str = ""
    notes: str = ""


def _init_feedback_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scan_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_hash TEXT NOT NULL,
            verdict_correct INTEGER NOT NULL,
            true_label TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@router.post("/feedback", dependencies=[Depends(require_api_key)])
def submit_feedback(item: FeedbackIn) -> dict:
    if not item.email_hash.strip():
        raise HTTPException(status_code=422, detail="email_hash must not be empty.")
    conn = get_connection()
    _init_feedback_table(conn)
    conn.execute(
        "INSERT INTO scan_feedback (email_hash, verdict_correct, true_label, notes) VALUES (?, ?, ?, ?)",
        (item.email_hash.strip(), int(item.verdict_correct), item.true_label[:50], item.notes[:2000]),
    )
    conn.commit()
    conn.close()
    return {"status": "recorded"}


@router.get("/feedback/stats", dependencies=[Depends(require_api_key)])
def feedback_stats() -> dict:
    conn = get_connection()
    _init_feedback_table(conn)
    total = conn.execute("SELECT COUNT(*) FROM scan_feedback").fetchone()[0]
    wrong = conn.execute("SELECT COUNT(*) FROM scan_feedback WHERE verdict_correct = 0").fetchone()[0]
    conn.close()
    return {
        "total_reviews": total,
        "reported_errors": wrong,
        "reported_error_rate": round(wrong / total, 4) if total else 0.0,
    }
