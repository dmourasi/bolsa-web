from __future__ import annotations

from fastapi import FastAPI

from bolsa_finder.web.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="bolsa-pos-finder", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
