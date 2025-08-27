Minimal FastAPI frontend
=======================

This is a minimal frontend for the backend app. It provides:

- Home page with a form to POST to `/add`
- Health page fetching `/db_health`
- Schema page fetching `/schema_summary`

Run locally
-----------

1) Create a venv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the backend (must listen on `http://localhost:8000` or set BACKEND_URL):

3) Start the frontend (from this directory):

```bash
cd frontend
uvicorn main:app --reload --port 8080
```

Environment
-----------

- `BACKEND_URL` (default `http://localhost:8000`) controls where API requests are sent.

Endpoints
---------

- `/` form to add a line (POST `/add`)
- `/health` shows DB health (`GET /db_health`)
- `/schema` shows schema summary (`GET /schema_summary`)


