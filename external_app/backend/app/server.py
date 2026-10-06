"""App entry point. Run with: uvicorn app.server:app"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

import app.models  # noqa: F401  (makes sure all models are registered)
from app.api.webhook import webhook_router
from app.api.v1.endpoints import contacts, kickoffs
from app.core.config import get_settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run code when the app starts: create the tables (and the SQLite file) if they do not exist."""
    Base.metadata.create_all(engine)
    yield


def create_app() -> FastAPI:
    """Build the FastAPI app and attach all routers."""
    application = FastAPI(
        title=get_settings().app_name,
        description=get_settings().app_description,
        lifespan=lifespan,
    )
    # Without CORS, the browser blocks the frontend from calling this API.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for resource in (contacts, kickoffs):
        application.include_router(resource.router, prefix=get_settings().api_v1_prefix)
    # Not under /api/v1: the flow host calls it (see api/webhook.py).
    application.include_router(webhook_router)

    @application.get("/", include_in_schema=False)
    def root():
        """Redirect the root URL to the contacts list."""
        return RedirectResponse(f"{get_settings().api_v1_prefix}/contacts")

    @application.get("/health", tags=["health"], summary="Health check")
    def health():
        """Return ok when the app is running."""
        return {"status": "ok"}

    return application


app = create_app()
