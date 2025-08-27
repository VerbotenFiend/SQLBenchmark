from typing import List, Tuple
from ..db import get_connection

def get_schema_rows() -> List[Tuple[str, str]]:
    sql = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
    ORDER BY table_name, ordinal_position;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        return [(r[0], r[1]) for r in cur.fetchall()]
    finally:
        conn.close()
