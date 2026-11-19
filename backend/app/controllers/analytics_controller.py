from backend.app.database.db import get_connection


def get_summary(owner: str = "anonymous") -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ?", (owner,)
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ? AND (prediction IN ('Phishing Email', 'Suspicious Email') OR risk_level = 'high')",
        (owner,),
    )
    phishing = cursor.fetchone()[0]

    cursor.execute(
        "SELECT AVG(confidence) FROM scan_history WHERE owner = ?", (owner,)
    )
    avg_conf = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM scan_history WHERE owner = ? AND email_text LIKE '%http%'",
        (owner,),
    )
    urls = cursor.fetchone()[0]

    conn.close()

    return {
        "scanned_emails": total,
        "phishing_detected": phishing,
        "average_risk_score": round(avg_conf, 1) if avg_conf else 0,
        "suspicious_urls": urls,
    }
