from typing import List
from fastapi import APIRouter
from ..models import SchemaRow
from ..logic.schema import get_schema_rows

router = APIRouter()

@router.get("/schema_summary", response_model=List[SchemaRow])
def schema_summary():
    rows = get_schema_rows()
    return [SchemaRow(table_name=t, table_column=c) for t, c in rows]
