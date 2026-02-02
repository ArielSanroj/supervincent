"""
Error handlers for the API.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def setup_error_handlers(app: FastAPI) -> None:
    """Setup error handlers for the FastAPI app."""

    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "detail": str(exc)}
        )

    @app.exception_handler(500)
    async def internal_error_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )
