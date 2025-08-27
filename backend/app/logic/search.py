from ..db import get_connection
import mariadb
from ..models import SqlRequest, SqlResponse

def sqlsearch(request: SqlRequest):
    validation = "invalid"
    res = None
    query = request.sql_query.strip()
    conn = get_connection()

    try:
        cur = conn.cursor()
        if (query.lower().startswith("select")):
            try:
                cur.execute(query)
                
                cur.execute(query)
                cols = [d[0] for d in cur.description] if cur.description else []
                rows = [list(r) for r in cur.fetchall()]
                res = {"columns": cols, "rows": rows}

                validation = "valid"
            except mariadb.Error as e:
                validation = "invalid"
        else:
            validation = "unsafe"

    except mariadb.Error as e:
        return SqlResponse(sql_validation=validation, results=None)

    finally:
        cur.close()
        conn.close()

    return SqlResponse(sql_validation=validation, results=res)