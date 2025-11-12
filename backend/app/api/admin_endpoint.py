from fastapi import APIRouter, HTTPException, Body
from ..db import get_admin_connection

router = APIRouter()

@router.post("/admin/execute_script")
def execute_script(sql_script: str = Body(..., embed=True)):
    conn = None
    try:
        conn = get_admin_connection()
        cur = conn.cursor()
        # Esegue l'intero script. NOTA: è potente ma rischioso!
        # L'utente può scrivere "DROP DATABASE..."!
        cur.execute(sql_script, multi_statement=True)
        return {"status": "ok", "message": "Script eseguito."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if conn: conn.close()


@router.get("/admin/list_databases")
def list_databases():
    conn = None
    try:
        conn = get_admin_connection()
        cur = conn.cursor()
        cur.execute("SHOW DATABASES")
        dbs = [row[0] for row in cur.fetchall()]
        # Filtra i database di sistema
        excluded_dbs = ["information_schema", "mysql", "performance_schema", "sys"]
        user_dbs = [db for db in dbs if db not in excluded_dbs]
        return {"databases": user_dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()