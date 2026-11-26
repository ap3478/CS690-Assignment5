"""Application factory (spec section 3).

Run with: uvicorn app.main:create_app --factory --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.repository import Repository
from app.routes import build_router
from app.service import BookingService

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def create_app(db_path: str = "roombook.db") -> FastAPI:
    """A RoomBook app that keeps all its data in the SQLite file at db_path."""
    repo = Repository(db_path)
    repo.init_db()
    service = BookingService(repo)

    # No /docs, /redoc or /openapi.json: the spec defines no such routes.
    app = FastAPI(title="RoomBook", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # R9: FastAPI's own 422s also use the error body.
        return JSONResponse(
            {"error": "invalid_request", "message": "The request is not valid."},
            status_code=422,
        )

    app.include_router(build_router(service))

    # Section 3 and D16: the page, as HTML, JavaScript and CSS. Only these three files.
    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(FRONTEND / "index.html", media_type="text/html")

    @app.get("/app.js", include_in_schema=False)
    async def app_js() -> FileResponse:
        return FileResponse(FRONTEND / "app.js", media_type="text/javascript")

    @app.get("/styles.css", include_in_schema=False)
    async def styles_css() -> FileResponse:
        return FileResponse(FRONTEND / "styles.css", media_type="text/css")

    return app
