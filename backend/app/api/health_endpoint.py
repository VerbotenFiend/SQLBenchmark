from fastapi import APIRouter
from ..models import Health
from ..logic.health import ping_db

router = APIRouter()

@router.get("/db_health", response_model=Health)
def db_health():
    ok = ping_db()
    return {"status": "ok" if ok else "down"}
