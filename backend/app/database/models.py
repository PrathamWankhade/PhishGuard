from backend.app.database.db import get_connection


def get_scan_history(owner=None):
    conn = get_connection()
    cursor = conn.cursor()

    if owner is None:
        cursor.execute("SELECT * FROM scan_history ORDER BY created_at DESC")
    else:
        cursor.execute(
            "SELECT * FROM scan_history WHERE owner = ? ORDER BY created_at DESC",
            (owner,),
        )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
