"""ASGI factory: uvicorn rag_toolkit.api.app:create_app --factory."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from rag_toolkit.api.models import (
    DocumentsRequest,
    DocumentsResponse,
    ErrorResponse,
    EvaluateRequest,
    HealthResponse,
    SearchRequest,
)
from rag_toolkit.api.service import RetrievalService
from rag_toolkit.schemas import EvalReport, SearchResponse

logger = logging.getLogger(__name__)


def create_app(config=None, *, pipeline=None) -> FastAPI:
    service = RetrievalService(pipeline=pipeline, config=config)
    app = FastAPI(
        title="RAG Toolkit API",
        version="0.1.0",
        responses={
            422: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    app.state.service = service

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [
            {"loc": list(e["loc"]), "message": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Invalid request",
                    "details": details,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={
                "error": {
                    "code": "http_error",
                    "message": str(exc.detail),
                    "details": [],
                }
            },
        )

    @app.exception_handler(Exception)
    async def internal_error(request: Request, exc: Exception):
        logger.error(
            "Request failed: %s %s (%s)",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Internal server error",
                    "details": [],
                }
            },
        )

    @app.middleware("http")
    async def sanitized_backend_boundary(request: Request, call_next):
        # Handle endpoint failures before ServerErrorMiddleware can re-raise them
        # into the ASGI server's raw exception logger. Public errors stay unchanged.
        try:
            return await call_next(request)
        except Exception as exc:
            return await internal_error(request, exc)

    @app.get("/health", response_model=HealthResponse)
    def health():
        return {"status": "ok", **service.stats()}

    @app.post("/documents", response_model=DocumentsResponse)
    def documents(request: DocumentsRequest):
        return service.add_documents(request.documents)

    @app.post("/search", response_model=SearchResponse)
    def search(request: SearchRequest):
        return service.search(request.query, request.top_k)

    @app.post("/evaluate", response_model=EvalReport)
    def evaluate(request: EvaluateRequest):
        return service.evaluate(request)

    return app
