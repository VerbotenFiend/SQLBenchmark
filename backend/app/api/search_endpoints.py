from fastapi import APIRouter
from app.models import SqlRequest, SearchRequest
from ..logic.search import sqlsearch

router = APIRouter()

@router.post("/sql_search")
def search(request: SqlRequest):
    return sqlsearch(request)

@router.post("/search")
def ask_ollama(request: SearchRequest):
    return