import os
import json
import httpx
from typing import Optional
from ..models import SqlRequest, SqlResponse
from ..config import OLLAMA_URL
from ..db import get_connection  # per leggere information_schema

# Config slide-friendly
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemma3:1b-it-qat")
FORCE_DEFAULT_MODEL = os.getenv("GROUP_SIZE", "2") == "2"  # se siete in 2, ignorate 'model' input

async def _ensure_model_available(model: str) -> None:
    """Verifica se il modello è installato. Se manca, lo scarica (pull) e ritorna quando disponibile."""
    async with httpx.AsyncClient(timeout=None) as client:
        # 1) controlla modelli presenti
        tags = await client.get(f"{OLLAMA_URL}/api/tags")
        if tags.status_code == 200:
            names = [m.get("name") for m in tags.json().get("models", [])]
            if model in names:
                return
        # 2) pull (non streaming per semplicità)
        resp = await client.post(f"{OLLAMA_URL}/api/pull",
                                 json={"name": model, "stream": False},
                                 headers={"Accept": "application/json"})
        resp.raise_for_status()
        # a questo punto il modello deve apparire in /api/tags

def _build_schema_prompt() -> str:
    """
    Costruisce un riassunto dello schema dal DB (information_schema),
    come richiesto dalle slide, da inserire nel prompt.
    """
    conn = get_connection()
    cur = conn.cursor()
    # Nota: limita a TABELLE del tuo schema corrente (database in uso)
    cur.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()

    # Aggrega per tabella
    schema = {}
    for table, col, typ in rows:
        schema.setdefault(table, []).append(f"{col} ({typ})")

    # Formattazione chiara e sintetica
    lines = []
    for table, cols in schema.items():
        cols_str = ", ".join(cols)
        lines.append(f"- {table}: {cols_str}")
    return "Schema del database:\n" + "\n".join(lines)

def _default_system_prompt() -> str:
    # Prompt minimale, in linea con le slide: “restituisci SOLO la query SQL”
    return (
        "Sei un esperto di SQL per MariaDB.\n"
        "Converti la richiesta dell'utente in una query SQL **solo SELECT** valida e sicura.\n"
        "RESTITUISCI SOLO la query SQL, senza commenti, testo o markdown."
    )

def _clean_sql_response(sql_response: str) -> str:
    # come la tua funzione corrente: togli block ```sql ... ```
    if "```sql" in sql_response:
        start = sql_response.find("```sql") + 6
        end = sql_response.find("```", start)
        if end != -1:
            sql_response = sql_response[start:end]
    elif "```" in sql_response:
        start = sql_response.find("```") + 3
        end = sql_response.find("```", start)
        if end != -1:
            sql_response = sql_response[start:end]

    # rimuovi commenti e righe vuote
    lines = [ln.strip() for ln in sql_response.split("\n")]
    lines = [ln for ln in lines if ln and not ln.startswith("--") and not ln.startswith("#")]
    return " ".join(lines).strip()

async def text_to_sql(
    text_query: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None
) -> str:
    """
    Converte una richiesta naturale in SQL, garantendo:
    - modello disponibile (auto-pull se manca),
    - prompt con schema dinamico (information_schema),
    - output SOLO query SQL (senza testo extra).
    """
    if FORCE_DEFAULT_MODEL:
        model = DEFAULT_MODEL  # slide: se gruppo da 2, usate sempre gemma3:1b-it-qat

    # 1) assicurati che il modello esista
    await _ensure_model_available(model)

    # 2) costruisci prompt con schema
    schema_text = _build_schema_prompt()
    sys = system_prompt or _default_system_prompt()
    prompt = f"{sys}\n\n{schema_text}\n\nRichiesta utente: {text_query}"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 500,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        # Se il modello non c'è (edge), prova una volta a pullare e ritentare
        if resp.status_code == 404:
            await _ensure_model_available(model)
            async with httpx.AsyncClient(timeout=None) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)

        resp.raise_for_status()
        data = resp.json()
        sql_raw = (data.get("response") or "").strip()
        return _clean_sql_response(sql_raw)

    except httpx.ConnectError:
        raise httpx.RequestError(f"Impossibile connettersi a Ollama su {OLLAMA_URL}")
    except httpx.TimeoutException:
        raise httpx.RequestError("Timeout nella richiesta a Ollama")
    except json.JSONDecodeError:
        raise ValueError("Risposta di Ollama non è un JSON valido")
    except Exception as e:
        # Lascia che il livello superiore gestisca l'errore impostando sql="" e sql_validation="error"
        raise Exception(f"Errore imprevisto durante la comunicazione con Ollama: {str(e)}")

# (opzionale) test connessione: usa sempre OLLAMA_URL (non localhost)
async def test_ollama_connection() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            return r.status_code == 200
    except:
        return False
