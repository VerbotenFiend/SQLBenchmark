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

class SqlResponse(BaseModel):
    sql_validation: str = Field(..., description="valid | invalid | unsafe")
    results: Optional[List[SqlResponseItem]] = Field(
        None, description="SQL search result: list of items or null when invalid/unsafe"
    )

class SearchRequest(BaseModel):
    question: str = Field(
        ...,
        description="Question asked in natural language to the model"
    )
    model: str = Field(
        ...,
        description="The chosen model to ask"
    )
    
class SearchResponse(BaseModel):
    sql : str = Field(
        "",
        description="LLM generated query"
    )
    sql_validation: str = Field(..., description="valid | invalid | unsafe")
    results: Optional[List[SqlResponseItem]] = Field(
        None, description="SQL search result: list of items or null when invalid/unsafe"
    )
    