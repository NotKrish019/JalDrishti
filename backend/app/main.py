"""BaoliGuard FastAPI Application Entrypoint.

Maintained by Swastik Parmar (Backend / Integration Engineer).
Phase 1 Foundation: Minimal, robust FastAPI application with typed routing,
strict CORS for local development, and contract validation boundaries.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings


def create_application() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.project_name,
        description=settings.description,
        version=settings.version,
    )

    # Restrict CORS to allowed development origins (defaults to http://localhost:5173)
    # Wildcard origins are strictly avoided for security and predictable development.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routing
    application.include_router(api_router)

    return application


app = create_application()
