from fastapi import APIRouter, Depends

from backend.app.database.models import get_scan_history
from backend.app.middleware.auth import require_api_key

router = APIRouter()


@router.get("/dashboard")
def dashboard(owner: str = Depends(require_api_key)):
    from backend.app.database.db import get_connection

    conn = get_connection()
    cur = conn.cursor()
    # Unique-email counts (one row per canonical email), scoped to caller.
    cur.execute("SELECT COUNT(*) FROM scan_history WHERE owner = ?", (owner,))
    unique_emails = cur.fetchone()[0]
    # Scan-event totals (rescans increment scan_count on the same row).
    cur.execute(
        "SELECT COALESCE(SUM(scan_count), 0) FROM scan_history WHERE owner = ?", (owner,)
    )
    total_scan_events = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ? AND prediction = 'Phishing Email'",
        (owner,),
    )
    phishing = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ? AND prediction = 'Suspicious Email'",
        (owner,),
    )
    suspicious = cur.fetchone()[0]
    cur.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ? AND prediction = 'Safe Email'", (owner,)
    )
    safe = cur.fetchone()[0]
    cur.execute(
        "SELECT AVG(confidence) FROM scan_history WHERE owner = ?", (owner,)
    )
    avg_conf = cur.fetchone()[0]
    levels = {"high": 0, "medium": 0, "low": 0}
    cur.execute(
        "SELECT risk_level, COUNT(*) FROM scan_history WHERE owner = ? GROUP BY risk_level",
        (owner,),
    )
    for risk, count in cur.fetchall():
        if risk in levels:
            levels[risk] = count
    conn.close()

    history = get_scan_history(owner=owner)
    total_scans = len(history)

    return {
        # Canonical KPIs: unique emails vs scan events are distinct measures.
        "unique_emails": unique_emails,
        "total_scan_events": total_scan_events,
        "total_scans": total_scans,
        "phishing_count": phishing,
        "suspicious_count": suspicious,
        "safe_count": safe,
        # Honestly named: the stored `confidence` column holds the policy risk
        # score. No `avg_confidence` alias — see the contract in API docs.
        "avg_risk_score": round(avg_conf, 1) if avg_conf else 0,
        "risk_levels": levels,
    }
