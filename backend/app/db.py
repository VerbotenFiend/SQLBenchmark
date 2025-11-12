import mariadb
from . import config
from typing import Any

def get_connection(database_name: str) -> mariadb.Connection: # Accetta un argomento
    return mariadb.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,       # Usa l'utente 'movies' (con permessi limitati)
        password=config.DB_PASSWORD,
        database=database_name,    # USA IL DATABASE PASSATO
        autocommit=False, 
    )
