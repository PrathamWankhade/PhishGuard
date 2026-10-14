from fastapi import APIRouter
from backend.app.database.models import (
    get_scan_history,
)

router = APIRouter()


@router.get("/dashboard")
def dashboard():
    from backend.app.database.db import get_connection

    conn = get_connection()
    cur = conn.cursor()
    # Unique-email counts (one row per canonical email).
    cur.execute("SELECT COUNT(*) FROM scan_history")
    unique_emails = cur.fetchone()[0]
    # Scan-event totals (rescans increment scan_count on the same row).
    cur.execute("SELECT COALESCE(SUM(scan_count), 0) FROM scan_history")
    total_scan_events = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scan_history WHERE prediction = 'Phishing Email'")
    phishing = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scan_history WHERE prediction = 'Suspicious Email'")
    suspicious = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM scan_history WHERE prediction = 'Safe Email'")
    safe = cur.fetchone()[0]
    cur.execute("SELECT AVG(confidence) FROM scan_history")
    avg_conf = cur.fetchone()[0]
    levels = {"high": 0, "medium": 0, "low": 0}
    cur.execute("SELECT risk_level, COUNT(*) FROM scan_history GROUP BY risk_level")
    for risk, count in cur.fetchall():
        if risk in levels:
            levels[risk] = count
    conn.close()

    history = get_scan_history()
    total_scans = len(history)

    return {
        # Canonical KPIs: unique emails vs scan events are distinct measures.
        "unique_emails": unique_emails,
        "total_scan_events": total_scan_events,
        "total_scans": total_scans,
        "phishing_count": phishing,
        "suspicious_count": suspicious,
        "safe_count": safe,
        "avg_confidence": round(avg_conf, 1) if avg_conf else 0,
        "risk_levels": levels,
    }