from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from bolsa_web.web.routes import router

STATIC_DIR = Path(__file__).resolve().parent.parent / "web_static"


def create_app() -> FastAPI:
    app = FastAPI(title="bolsa-pos-finder", version="0.1.0")
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html; charset=utf-8")

    # Liveness only: no external source is queried, so the platform's health check stays cheap.
    @app.get("/healthz", include_in_schema=False)
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
