from fastapi import APIRouter
from app.models import SqlRequest, SearchRequest, SearchResponse
from ..logic.search import sqlsearch, llmsearch
from typing import Any

router = APIRouter()

@router.post("/sql_search")
def sql_search(request: SqlRequest) -> Any: 
    return sqlsearch(request)

@router.post("/search", response_model=SearchResponse)
async def ask_ollama(request: SearchRequest) -> SearchResponse:
    return await llmsearch(request)

