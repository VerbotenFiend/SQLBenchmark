import os, sys, time, csv
import mariadb
from .logic.add import add_line  
from . import config

DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_NAME = config.DB_NAME

TSV_PATH = os.getenv("SEED_TSV", "/seed/data.tsv")

from .db import get_connection

def wait_for_db(retries: int = 60, delay: float = 2.0) -> None:
    for i in range(retries):
        try:
            conn = get_connection()
            conn.close()
            return
        except mariadb.Error:
            time.sleep(delay)
    print("DB not responding after several tries", file=sys.stderr)
    sys.exit(1)

# controllo se in movies c'è qualcosa; se sì, è già popolato
def db_has_data() -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM movies")
        (n,) = cur.fetchone()
        return n > 0
    finally:
        conn.close()

# apre tsv, check header (tenta la conversione col 3,4 in numeri), crea data_line csv e chiama add
def seed_from_tsv(tsv_path: str) -> None:
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
                print(f"[row {idx}] columns given: {row}", file=sys.stderr)
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
                print(f"[riga {idx}] ERROR: {e}", file=sys.stderr)
    print(f"Seed completed. Inserted: {inserted}, errors: {errors}, skipped: {skipped}")

if __name__ == "__main__":
    if not os.path.exists(TSV_PATH):
        print(f"File TSV not found: {TSV_PATH}", file=sys.stderr)
        sys.exit(0)

    wait_for_db()

    if db_has_data():
        print("DB is already populated: seed skipped.")
        sys.exit(0)

    seed_from_tsv(TSV_PATH)
