from fastapi import APIRouter, HTTPException
from app.models import SqlRequest
from ..logic.search import sqlsearch

router = APIRouter()

@router.post("/sql_search")
def search(request: SqlRequest):
    return sqlsearch(request)