from pydantic import BaseModel, Field
from typing import List, Optional

class SchemaRow(BaseModel):
    table_name: str
    table_column: str

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
    property_value: str

class SqlResponseItem(BaseModel):
    item_type: str
    properties: List[Property]

class SqlRequest(BaseModel):
    sql_query: str = Field(
        ..., 
        description="Sql query to execute")
    database_name: str = Field(..., description="Database to run query against")

class SqlResponse(BaseModel):
    sql_validation: str = Field(..., description="valid | invalid | unsafe")
    results: Optional[List[SqlResponseItem]] = Field(
        None, description="SQL search result: list of items or null when invalid/unsafe"
    )


    