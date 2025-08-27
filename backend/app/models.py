from pydantic import BaseModel, Field
from typing import List, Any

class SchemaRow(BaseModel):
    table_name: str
    column_name: str

class Health(BaseModel):
    status: str

class AddRequest(BaseModel):
    data_line: str = Field(
        ...,
        description="Titolo,Regista,Età,Anno,Genere,Piattaforma_1,Piattaforma_2"
    )

class StatusOk(BaseModel):
    status: str = "ok"

class Property(BaseModel):
    property_name: str
    property_value: str  # se vuoi supportare NULL veri, valuta Optional[str]

class SearchResponseItem(BaseModel):
    item_type: str
    properties: List[Property]

class SqlRequest(BaseModel):
    sql_query: str = Field(..., description="Sql query to execute")

class SqlResponse(BaseModel):
    sql_validation: str = Field(..., description="valid | invalid | unsafe")
    results: List[SearchResponseItem] = Field(
        ..., description="SQL search result: array of items"
    )

