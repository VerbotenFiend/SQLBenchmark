# backend/app/ingest_tsv.py
import os, sys, time, csv
import mariadb
from .logic.add import add_line  # presa da endpoint add
from . import config

# lettura var di ambiente
DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_NAME = config.DB_NAME

TSV_PATH = os.getenv("SEED_TSV", "/seed/data.tsv")

from .db import get_connection

def wait_for_db(retries=60, delay=2.0):
    for i in range(retries):
        try:
            conn = get_connection()
            conn.close()
            return
        except mariadb.Error:
            time.sleep(delay)
    print("DB non raggiungibile dopo i tentativi previsti", file=sys.stderr)
    sys.exit(1)

# controllo se in movies c'è qualcosa; se sì, è già popolato
def db_has_data():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies")
        (n,) = cur.fetchone()
        return n > 0
    finally:
        conn.close()

# apre tsv, check header (tenta la conversione col 3,4 in numeri), crea data_line csv e chiama add
def seed_from_tsv(tsv_path: str):
    inserted, skipped, errors = 0, 0, 0
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header_peek = next(reader)
        maybe_header = False
        try:
            int(header_peek[2]); int(header_peek[3])
        except Exception:
            maybe_header = True
        if not maybe_header:
            row = header_peek
            rows_iter = [row] + list(reader)
        else:
            rows_iter = list(reader)

        for idx, row in enumerate(rows_iter, start=1):
            # atteso: 7 colonne [titolo, regista, eta, anno, genere, p1, p2]
            if len(row) < 5:
                errors += 1
                print(f"[riga {idx}] colonne insufficienti: {row}", file=sys.stderr)
                continue
            # normalizza a 7 campi
            row = (row + ["", ""])[:7]
            titolo, regista, eta, anno, genere, p1, p2 = [c.strip() for c in row]

            data_line = ",".join([titolo, regista, eta, anno, genere, p1, p2])
            try:
                add_line(data_line)
                inserted += 1
            except Exception as e:
                errors += 1
                print(f"[riga {idx}] ERRORE: {e}", file=sys.stderr)
    print(f"Seed completato. Inserite: {inserted}, errori: {errors}, saltate: {skipped}")

if __name__ == "__main__":
    if not os.path.exists(TSV_PATH):
        print(f"File TSV non trovato: {TSV_PATH}", file=sys.stderr)
        sys.exit(0)  # non fallire l'app se manca il seed

    wait_for_db()

    if db_has_data():
        print("DB già popolato: seed saltato.")
        sys.exit(0)

    seed_from_tsv(TSV_PATH)
