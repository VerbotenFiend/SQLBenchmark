from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routes import router as ui_router


def create_app() -> FastAPI:
	app = FastAPI(title="Frontend Minimal")
	app.mount("/static", StaticFiles(directory=str((__file__[: __file__.rfind("/")] + "/static"))), name="static")
	app.include_router(ui_router)
	return app


app = create_app()


