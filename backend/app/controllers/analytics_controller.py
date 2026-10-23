from backend.app.database.db import get_connection


def get_summary() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scan_history")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scan_history WHERE prediction IN ('Phishing Email', 'Suspicious Email') OR risk_level = 'high'")
    phishing = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(confidence) FROM scan_history")
    avg_conf = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scan_history WHERE email_text LIKE '%http%'")
    urls = cursor.fetchone()[0]

    conn.close()

    return {
        "scanned_emails": total,
        "phishing_detected": phishing,
        "average_risk_score": round(avg_conf, 1) if avg_conf else 0,
        "suspicious_urls": urls,
    }
