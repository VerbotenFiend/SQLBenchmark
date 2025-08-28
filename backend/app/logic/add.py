from typing import List, Optional, Tuple
import mariadb
from ..db import get_connection

# -------- parsing & validation ---------------------------------------------

def _parse_data_line(data_line: str) -> Tuple[str, str, int, int, str, List[str]]:
    parts = [p.strip() for p in data_line.split(",")]
    if len(parts) != 7:
        raise ValueError(f"Number of fields expected = 7, found = {len(parts)}")

    titolo, nome_regista, eta_s, anno_s, genere, p1, p2 = parts

    if not titolo:
        raise ValueError("Missing 'titolo'")
    if not nome_regista:
        raise ValueError("'nome' missing")
    if not genere:
        raise ValueError("'genere' missing")

    try:
        eta = int(eta_s)
    except ValueError:
        raise ValueError("'eta' must be an integer")

    try:
        anno = int(anno_s)
    except ValueError:
        raise ValueError("'anno' must be an integer")

    piattaforme: List[str] = []
    for p in (p1, p2):
        p = (p or "").strip()
        if p:
            piattaforme.append(p)

    seen = set()
    dedup = []
    for p in piattaforme:
        k = p.lower()
        if k not in seen:
            seen.add(k)
            dedup.append(p)
    piattaforme = dedup[:2]

    return titolo, nome_regista, eta, anno, genere, piattaforme

# -------- DB helper ----------------------------------------------------------

def _get_or_create_regista(cur, nome: str, eta: int) -> int:
    cur.execute("SELECT idR FROM regista WHERE nome = ?", (nome,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE regista SET eta=? WHERE idR=?", (eta, row[0]))
        return row[0]
    cur.execute("INSERT INTO regista (nome, eta) VALUES (?, ?)", (nome, eta))
    return cur.lastrowid

def _get_or_create_piattaforma(cur, nome: str) -> int:
    cur.execute("SELECT idP FROM piattaforma WHERE nome = ?", (nome,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("INSERT INTO piattaforma (nome) VALUES (?)", (nome,))
    return cur.lastrowid

def _upsert_film(cur, titolo: str, idR: int, anno: int, genere: str) -> int:
    cur.execute("SELECT idF FROM movies WHERE titolo = ?", (titolo,))
    row = cur.fetchone()
    if row:
        cur.execute(
            "UPDATE movies SET idR=?, anno=?, genere=? WHERE idF=?",
            (idR, anno, genere, row[0])
        )
        return row[0]
    cur.execute(
        "INSERT INTO movies (titolo, idR, anno, genere) VALUES (?, ?, ?, ?)",
        (titolo, idR, anno, genere)
    )
    return cur.lastrowid

def _replace_piattaforme(cur, idF: int, piattaforme: List[str]):

    cur.execute("SELECT idF FROM dove_vederlo WHERE idF=?", (idF,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO dove_vederlo (idF, idP1, idP2) VALUES (?, NULL, NULL)",
            (idF,)
        )

    cur.execute(
        "UPDATE dove_vederlo SET idP1=NULL, idP2=NULL WHERE idF=?",
        (idF,)
    )

    ids: List[Optional[int]] = []
    for p in piattaforme[:2]:
        pid = _get_or_create_piattaforma(cur, p)
        ids.append(pid)

    if len(ids) >= 1:
        cur.execute("UPDATE dove_vederlo SET idP1=? WHERE idF=?", (ids[0], idF))
    if len(ids) == 2:
        cur.execute("UPDATE dove_vederlo SET idP2=? WHERE idF=?", (ids[1], idF))

# -------- entrypoint ---------------------------------------------------------

def add_line(data_line: str) -> None:
    titolo, nome_regista, eta, anno, genere, piattaforme = _parse_data_line(data_line)

    conn = get_connection()
    try:
        cur = conn.cursor()
        idR = _get_or_create_regista(cur, nome_regista, eta)
        idF = _upsert_film(cur, titolo, idR, anno, genere)
        _replace_piattaforme(cur, idF, piattaforme)
        conn.commit()
    except mariadb.Error as e:
        conn.rollback()
        raise ValueError(f"DB error: {e}")
    finally:
        conn.close()
