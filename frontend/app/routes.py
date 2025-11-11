from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple


router = APIRouter()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
templates = Jinja2Templates(directory=str((__file__[: __file__.rfind("/")] + "/templates")))

def _normalize_results(res: Any) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Normalizza i risultati in (columns, rows).
    - Se res è una lista di dict: columns = keys del primo, rows = la lista
    - Se res ha 'columns' e 'rows': prova a mappare rows come lista di dict
    - Altrimenti ritorna ([], [])
    """
    if not res:
        return [], []
    if isinstance(res, list):
        first = res[0] if res else {}
        if isinstance(first, dict):
            cols = list(first.keys())
            return cols, res
        cols = [str(i) for i in range(len(first))] if first else []
        rows = [list(r) for r in res]
        return cols, rows
    if isinstance(res, dict) and "columns" in res and "rows" in res:
        cols = res["columns"] or []
        rows_ll = res["rows"] or []
        mapped = []
        for r in rows_ll:
            if isinstance(r, dict):
                mapped.append(r)
            else:
                mapped.append({c: (r[i] if i < len(r) else None) for i, c in enumerate(cols)})
        return cols, mapped
    return [], []

@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request, "title": "Text→SQL UI"})

@router.get("/health", response_class=HTMLResponse)
async def health(request: Request) -> HTMLResponse:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BACKEND_URL}/db_health")
        data = resp.json()
    return templates.TemplateResponse("health.html", {"request": request, "data": data})

# === SCHEMA ===
@router.get("/schema", response_class=HTMLResponse)
async def schema(request: Request) -> HTMLResponse:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{BACKEND_URL}/schema_summary")
        rows = resp.json()
    return templates.TemplateResponse("schema.html", {"request": request, "rows": rows})

# === ADD/UPDATE ===
@router.post("/add")
async def add_line(request: Request):
    form = await request.form()
    data_line = form.get("data_line", "")
    if not data_line:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(f"{BACKEND_URL}/add", json={"data_line": data_line})
        if resp.status_code == 200:
            return RedirectResponse(url="/schema", status_code=status.HTTP_302_FOUND)
        else:
            # show error on home
            error = resp.json().get("detail", "Unknown error")
            return templates.TemplateResponse("index.html", {"request": request, "error": error, "data_line": data_line})

# === ADD/UPDATE : ritorna JSON con esito ===
@router.post("/ui/add", response_class=JSONResponse)
async def add_line_modal(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "JSON body missing or invalid"}, status_code=400)

    data_line = (payload.get("data_line") or "").strip()
    if not data_line:
        return JSONResponse({"ok": False, "error": "data_line is missing"}, status_code=400)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/add",
                json={"data_line": data_line},
                headers={"Accept": "application/json"},
            )
    except httpx.RequestError as e:
        return JSONResponse({"ok": False, "error": f"Backend error: {e}"}, status_code=502)

    if resp.status_code in (200, 201):
        return JSONResponse({"ok": True})

    # estrai un messaggio leggibile se il backend risponde errore
    try:
        detail = resp.json().get("detail")
    except Exception:
        detail = resp.text
    return JSONResponse({"ok": False, "error": detail or f"Backend {resp.status_code}"}, status_code=422)

# === SQL diretto: ritorna un frammento HTML da appendere al feed ===
@router.post("/ui/sql", response_class=HTMLResponse)
async def ui_sql(request: Request) -> HTMLResponse:
    form = await request.form()
    sql_query = form.get("sql_query", "").strip()
    if not sql_query:
        return HTMLResponse("<div class='bubble'><span class='badge invalid'>Errore</span> SQL mancante.</div>", status_code=400)

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{BACKEND_URL}/sql_search", json={"sql_query": sql_query})
        data = resp.json()

    sql_validation = data.get("sql_validation")
    results = data.get("results")

    columns, rows = ([], [])
    if sql_validation == "valid" and results is not None:
        columns, rows = _normalize_results(results)

    return templates.TemplateResponse(
        "_result_row.html",
        {
            "request": request,
            "mode": "SQL",
            "when": datetime.now().strftime("%H:%M"),
            "sql": sql_query,
            "sql_validation": sql_validation,
            "columns": columns,
            "rows": rows,
            # "kv_blocks": kv_blocks,   
        },
)

