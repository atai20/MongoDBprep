from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from matcharena import __version__
from matcharena.api.errors import install_error_handlers
from matcharena.api.routes import build_api_router
from matcharena.config import Settings, load_settings
from matcharena.container import Container, build_container
from matcharena.db.indexes import ensure_indexes
from matcharena.logging_setup import configure_logging


def create_app(
    settings: Settings | None = None,
    container: Container | None = None,
) -> FastAPI:
    configure_logging()
    settings = settings or load_settings()
    container = container or build_container(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if settings.init_indexes_on_startup:
            ensure_indexes(container.db)
        yield

    app = FastAPI(
        title="MatchArena",
        version=__version__,
        description="Player matchmaking, queueing and game lobbies.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.container = container

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_error_handlers(app)
    app.include_router(build_api_router())
    return app
