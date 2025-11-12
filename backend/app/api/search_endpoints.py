from fastapi import APIRouter
from app.models import SqlRequest
from ..logic.search import sqlsearch
from typing import Any

router = APIRouter()

@router.post("/sql_search")
def sql_search(request: SqlRequest) -> Any: 
    return sqlsearch(request)


