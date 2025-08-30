import mariadb
from . import config
from typing import Any

def get_connection() -> mariadb.Connection:
    return mariadb.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        autocommit=False, 
    )
