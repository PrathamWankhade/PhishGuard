from backend.app.database.db import get_connection


def get_scan_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM scan_history
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]