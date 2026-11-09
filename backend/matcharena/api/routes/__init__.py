from fastapi import APIRouter

from matcharena.api.routes.auth import router as auth_router
from matcharena.api.routes.games import router as games_router
from matcharena.api.routes.health import router as health_router
from matcharena.api.routes.matchmaking import router as matchmaking_router
from matcharena.api.routes.ops import router as ops_router
from matcharena.api.routes.players import router as players_router


def build_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(auth_router)
    router.include_router(players_router)
    router.include_router(matchmaking_router)
    router.include_router(games_router)
    router.include_router(ops_router)
    return router
