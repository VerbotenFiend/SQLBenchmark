from ..db import get_connection
import mariadb
from ..models import SqlRequest, SqlResponse
import re

def _infer_item_type(sql: str) -> str:
    m = re.search(r"\bfrom\s+([`\"]?)(\w+)\1\b", sql, flags=re.IGNORECASE)
    return (m.group(2) if m else "item")

def sqlsearch(request: SqlRequest):
    query = request.sql_query.strip()
    validation = "unsafe"
    results = None

    if query.lower().startswith("select"):
        validation = "invalid" 

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query)

            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchall()

            item_type = getattr(request, "item_type", None) or _infer_item_type(query)

            formatted = []
            for row in rows:
                props = []
                for name, value in zip(cols, row):
                    props.append({
                        "property_name": str(name),
                        "property_value": None if value is None else str(value)
                    })
                formatted.append({
                    "item_type": item_type,
                    "properties": props
                })

            results = formatted
            validation = "valid"

        except mariadb.Error:
            validation = "invalid"
        finally:
            cur.close()
            conn.close()
    else:
        validation = "unsafe"

    return SqlResponse(sql=query, sql_validation=validation, results=results)
