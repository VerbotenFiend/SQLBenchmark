from fastapi import APIRouter
from app.models import SqlRequest, SearchRequest, SearchResponse
from ..logic.search import sqlsearch, llmsearch

router = APIRouter()

@router.post("/sql_search")
def sql_search(request: SqlRequest): 
    return sqlsearch(request)

@router.post("/search", response_model=SearchResponse)
async def ask_ollama(request: SearchRequest):  # <- async
    return await llmsearch(request)            # <- await

