from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
import os
from datetime import datetime
#aggiunta per prova
# --- in cima a routes.py (dopo gli import esistenti) ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")  # su Docker network
USE_OLLAMA_CHAT = os.getenv("USE_OLLAMA_CHAT", "true").lower() == "true"

router = APIRouter()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
templates = Jinja2Templates(directory=str((__file__[: __file__.rfind("/")] + "/templates")))

def _normalize_results(res):
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
        # lista di liste/tuple: deduciamo colonne numeriche
        cols = [str(i) for i in range(len(first))] if first else []
        rows = [list(r) for r in res]
        return cols, rows
    if isinstance(res, dict) and "columns" in res and "rows" in res:
        cols = res["columns"] or []
        rows_ll = res["rows"] or []
        # prova a mappare rows (lista di liste) a lista di dict
        mapped = []
        for r in rows_ll:
            if isinstance(r, dict):
                mapped.append(r)
            else:
                mapped.append({c: (r[i] if i < len(r) else None) for i, c in enumerate(cols)})
        return cols, mapped
    return [], []

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Text→SQL UI"})

@router.get("/health", response_class=HTMLResponse)
async def health(request: Request):
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BACKEND_URL}/db_health")
        data = resp.json()
    return templates.TemplateResponse("health.html", {"request": request, "data": data})

# === SCHEMA: frammento per il modal ===
@router.get("/schema", response_class=HTMLResponse)
async def schema(request: Request):
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{BACKEND_URL}/schema_summary")
        rows = resp.json()
    return templates.TemplateResponse("schema.html", {"request": request, "rows": rows})

# === ADD/UPDATE (fallback no-JS: redirect a /schema) ===
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

# === ADD/UPDATE per modal (JS): ritorna JSON con esito ===
@router.post("/ui/add", response_class=JSONResponse)
async def add_line_modal(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"ok": False, "error": "Body JSON mancante/non valido"}, status_code=400)

    data_line = (payload.get("data_line") or "").strip()
    if not data_line:
        return JSONResponse({"ok": False, "error": "Campo data_line mancante"}, status_code=400)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{BACKEND_URL}/add",
                json={"data_line": data_line},
                headers={"Accept": "application/json"},
            )
    except httpx.RequestError as e:
        return JSONResponse({"ok": False, "error": f"Errore di rete verso backend: {e}"}, status_code=502)

    if resp.status_code in (200, 201):
        return JSONResponse({"ok": True})

    # estrai un messaggio leggibile se il backend risponde errore
    try:
        detail = resp.json().get("detail")
    except Exception:
        detail = resp.text
    return JSONResponse({"ok": False, "error": detail or f"Backend {resp.status_code}"}, status_code=422)

# # === SEARCH (LLM → SQL): ritorna un frammento HTML da appendere al feed ===
# @router.post("/ui/search", response_class=HTMLResponse)
# async def ui_search(request: Request):
#     form = await request.form()
#     question = form.get("question", "").strip()

#     model = form.get("model", "gemma3:1b-it-qat")

#     if not question:
#         return HTMLResponse("<div class='bubble'><span class='badge invalid'>Errore</span> Domanda mancante.</div>", status_code=400)

#     async with httpx.AsyncClient(timeout=60.0) as client:
#         resp = await client.post(f"{BACKEND_URL}/search", json={"question": question, "model": model})
#         data = resp.json()

#     sql = data.get("sql")
#     sql_validation = data.get("sql_validation") or data.get("sql validation")  # tollera entrambe
#     results = data.get("results")

#     columns, rows = ([], [])
#     if sql_validation == "valid" and results is not None:
#         columns, rows = _normalize_results(results)

#     return templates.TemplateResponse(
#         "_result_row.html",
#         {
#             "request": request,
#             "mode": "LLM",
#             "when": datetime.now().strftime("%H:%M"),
#             "sql": sql,
#             "sql_validation": sql_validation,
#             "columns": columns,
#             "rows": rows,
#         },
#     )

# === SQL diretto: ritorna un frammento HTML da appendere al feed ===
@router.post("/ui/sql", response_class=HTMLResponse)
async def ui_sql(request: Request):
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


    kv_blocks = []
    if sql_validation == "valid" and results:
        if isinstance(results, list) and isinstance(results[0], dict) and "properties" in results[0]:
            for item in results:
                props = item.get("properties") or []
                block = [{"name": str(p.get("property_name", "")),
                      "value": p.get("property_value", "")} for p in props]
                if block:
                    kv_blocks.append(block)

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
            "kv_blocks": kv_blocks,   
        },
)

##PROVA
# @router.post("/ui/search", response_class=HTMLResponse)
# async def ui_search(request: Request):
#     form = await request.form()
#     question = form.get("question", "").strip()
#     model = form.get("model", "gemma3:1b-it-qat")

#     if not question:
#         return HTMLResponse("<div class='bubble'><span class='badge invalid'>Errore</span> Domanda mancante.</div>", status_code=400)

#     # --- Modalità CHAT con Ollama: bypass del backend Text-to-SQL ---
#     if USE_OLLAMA_CHAT:
#         try:
#             payload = {
#                 "model": model,
#                 "messages": [
#                     {"role": "system", "content": "Sei un assistente utile. Rispondi in modo conciso."},
#                     {"role": "user", "content": question}
#                 ],
#                 "stream": False
#             }
#             async with httpx.AsyncClient(timeout=120.0) as client:
#                 resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload, headers={"Accept": "application/json"})
#                 resp.raise_for_status()
#                 data = resp.json()
#             # L'output utile sta in data["message"]["content"]
#             content = (data.get("message") or {}).get("content", "").strip()
#             # Riutilizziamo il frammento esistente: mettiamo la risposta in "sql" e niente tabella
#             return templates.TemplateResponse(
#                 "_result_row.html",
#                 {
#                     "request": request,
#                     "mode": "LLM",
#                     "when": datetime.now().strftime("%H:%M"),
#                     "sql": content,            # <— mostriamo il testo della risposta qui
#                     "sql_validation": "valid",  # badge verde per non farla sembrare un errore
#                     "columns": [],
#                     "rows": [],
#                 },
#             )
#         except httpx.RequestError as e:
#             return HTMLResponse(f"<div class='bubble'><span class='badge invalid'>Errore</span> Connessione a Ollama fallita: {e}</div>", status_code=502)
#         except Exception as e:
#             return HTMLResponse(f"<div class='bubble'><span class='badge invalid'>Errore</span> {e}</div>", status_code=500)

#     # --- Modalità originale Text-to-SQL: chiama il backend ---
#     async with httpx.AsyncClient(timeout=60.0) as client:
#         resp = await client.post(f"{BACKEND_URL}/search", json={"question": question, "model": model})
#         data = resp.json()

#     sql = data.get("sql")
#     sql_validation = data.get("sql_validation") or data.get("sql validation")
#     results = data.get("results")

#     columns, rows = ([], [])
#     if sql_validation == "valid" and results is not None:
#         columns, rows = _normalize_results(results)


#     kv_blocks = []
#     if sql_validation == "valid" and results:
#         if isinstance(results, list) and isinstance(results[0], dict) and "properties" in results[0]:
#             for item in results:
#                 props = item.get("properties") or []
#                 block = [{"name": str(p.get("property_name", "")),
#                       "value": p.get("property_value", "")} for p in props]
#                 if block:
#                     kv_blocks.append(block)

#     return templates.TemplateResponse(
#         "_result_row.html",
#         {
#             "request": request,
#             "mode": "LLM",
#             "when": datetime.now().strftime("%H:%M"),
#             "sql": sql,
#             "sql_validation": sql_validation,
#             "columns": columns,
#             "rows": rows,
#             "kv_blocks": kv_blocks,   
#         },
# )

