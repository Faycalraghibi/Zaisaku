"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from zaisaku.api.routers import documents, health, ingest, query
from zaisaku.config import Settings


def create_app(config: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        from zaisaku.config import get_settings
        config = get_settings()

    app = FastAPI(
        title="Zaisaku API",
        description="RAG Pipeline for Financial Documents",
        version="0.1.0",
        # Route Swagger UI to /api/docs to match README
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # We prefix all routes with /api to match frontend expectations
    app.include_router(health.router, prefix="/api")
    app.include_router(ingest.router, prefix="/api")
    app.include_router(query.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")

    return app
