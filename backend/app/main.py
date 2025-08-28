from fastapi import FastAPI
from .api.health_endpoint import router as health_router
from .api.schema_endpoint import router as schema_router
from .api.add_endpoints import router as add_router
from .api.search_endpoints import router as search_router

app = FastAPI(title="Esonero Backend")

app.include_router(health_router)
app.include_router(schema_router)
app.include_router(add_router)
app.include_router(search_router)
