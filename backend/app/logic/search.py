from ..db import get_connection
import mariadb
import re
from ..models import SqlRequest, SqlResponse, Property, SearchResponseItem
from typing import Optional, List

def _infer_item_type(sql: str) -> str:
    m = re.search(r"\bfrom\s+([`\"]?)(\w+)\1\b", sql, flags=re.IGNORECASE)
    return (m.group(2) if m else "item")

def sqlsearch(request: SqlRequest) -> SqlResponse:
    validation = "invalid"
    results: List[SearchResponseItem] = []
    query = request.sql_query.strip()

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        if query.lower().startswith("select"):
            try:
                cur.execute(query)

                desc = cur.description  
                if not desc:
                    validation = "valid"
                    return SqlResponse(sql_validation=validation, results=results)

                column_names = [d[0] for d in desc]
                rows = cur.fetchall()  

                item_type = _infer_item_type(query)

                for row in rows:
                    properties_list: List[Property] = []
                    for col_name, value in zip(column_names, row):
                        properties_list.append(Property(
                            property_name=str(col_name),
                            property_value="" if value is None else str(value)
                        ))

                    results.append(SearchResponseItem(
                        item_type=item_type,
                        properties=properties_list
                    ))

                validation = "valid"

            except mariadb.Error:
                validation = "invalid"
        else:
            validation = "unsafe"

    except mariadb.Error:
        # Mantieni "invalid" e results vuoto
        return SqlResponse(sql_validation=validation, results=results)

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    return SqlResponse(sql_validation=validation, results=results)
