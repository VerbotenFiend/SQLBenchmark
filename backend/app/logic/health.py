from ..db import get_connection

def ping_db() -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchall()
        return True
    finally:
        conn.close()
