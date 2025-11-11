import os
from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3307"))
DB_USER = os.getenv("DB_USER", "movies")
DB_PASSWORD = os.getenv("DB_PASSWORD", "moviespwd")
DB_NAME = os.getenv("DB_NAME", "moviesdb")

APP_PORT = int(os.getenv("APP_PORT", "8003"))
