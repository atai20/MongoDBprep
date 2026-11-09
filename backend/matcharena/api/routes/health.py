from __future__ import annotations

from fastapi import APIRouter, Depends

from matcharena.api.deps import get_container
from matcharena.container import Container
from matcharena.coordination.redis_client import ping as redis_ping
from matcharena.db.mongo import ping as mongo_ping

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "matcharena"}


@router.get("/api/health/ready")
def ready(container: Container = Depends(get_container)) -> dict:
    mongo_ok = mongo_ping(container.db)
    redis_ok = redis_ping(container.redis)
    return {
        "status": "ok" if mongo_ok and redis_ok else "degraded",
        "mongo": mongo_ok,
        "redis": redis_ok,
        "database": container.settings.mongo_db,
    }
