import httpx
import json
from typing import Optional, Dict, Any
from ..models import SqlRequest, SqlResponse
from ..config import OLLAMA_URL

async def text_to_sql(text_query: str, model: str = "gemma3:1b-it-qat", system_prompt: Optional[str] = None) -> str:
    """
    Converte una query in linguaggio naturale in SQL usando Ollama.
    
    Args:
        text_query: La query in linguaggio naturale (es. "trova tutte le proprietà a Milano")
        model: Il modello Ollama da utilizzare (default: "gemma3:1b-it-qat")
        system_prompt: Prompt di sistema opzionale per guidare la generazione
    
    Returns:
        La query SQL generata
        
    Raises:
        requests.RequestException: Se c'è un errore di connessione
        ValueError: Se la risposta di Ollama non è valida
    """
    
    # Configurazione di base
    OLLAMA_BASE_URL = OLLAMA_URL
    
    # Prompt di sistema di default se non specificato
    if system_prompt is None:
        system_prompt = """Sei un esperto di SQL. Converti la richiesta dell'utente in una query SQL valida.
        Restituisci SOLO la query SQL, senza spiegazioni o commenti aggiuntivi."""
    
    # Preparazione della richiesta per Ollama
    payload = {
        "model": model,
        "prompt": f"{system_prompt}\n\nRichiesta utente: {text_query}",
        "stream": False,
        "options": {
            "temperature": 0.1,  # Bassa temperatura per risposte più deterministiche
            "top_p": 0.9,
            "max_tokens": 500
        }
    }
    
    try:
        # Invio della richiesta a Ollama
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
        
        # Controllo dello status code
        response.raise_for_status()
        
        # Parsing della risposta
        response_data = response.json()
        
        # Estrazione della risposta generata
        if "response" in response_data:
            sql_query = response_data["response"].strip()
            
            # Pulizia della risposta (rimozione di markdown, commenti extra, ecc.)
            sql_query = clean_sql_response(sql_query)
            
            return sql_query
        else:
            raise ValueError("Risposta di Ollama non valida: campo 'response' mancante")
            
    except httpx.ConnectError:
        raise httpx.RequestError("Impossibile connettersi a Ollama. Assicurati che sia in esecuzione su localhost:11434")
    except httpx.TimeoutException:
        raise httpx.RequestError("Timeout nella richiesta a Ollama")
    except json.JSONDecodeError:
        raise ValueError("Risposta di Ollama non è un JSON valido")
    except Exception as e:
        raise Exception(f"Errore imprevisto durante la comunicazione con Ollama: {str(e)}")

def clean_sql_response(sql_response: str) -> str:
    """
    Pulisce la risposta SQL da Ollama rimuovendo markdown e commenti extra.
    
    Args:
        sql_response: La risposta grezza da Ollama
        
    Returns:
        La query SQL pulita
    """
    # Rimozione di markdown code blocks
    if "```sql" in sql_response:
        start = sql_response.find("```sql") + 6
        end = sql_response.find("```", start)
        if end != -1:
            sql_response = sql_response[start:end]
    
    # Rimozione di code blocks generici
    elif "```" in sql_response:
        start = sql_response.find("```") + 3
        end = sql_response.find("```", start)
        if end != -1:
            sql_response = sql_response[start:end]
    
    # Rimozione di commenti extra e spazi bianchi
    lines = sql_response.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # Salta linee vuote o commenti
        if line and not line.startswith('--') and not line.startswith('#'):
            cleaned_lines.append(line)
    
    return ' '.join(cleaned_lines).strip()

# Funzione di utilità per testare la connessione a Ollama
async def test_ollama_connection() -> bool:
    """
    Testa la connessione a Ollama.
    
    Returns:
        True se Ollama è raggiungibile, False altrimenti
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except:
        return False

