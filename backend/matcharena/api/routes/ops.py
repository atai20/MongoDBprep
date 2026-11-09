from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from matcharena.api.deps import get_container
from matcharena.container import Container
from matcharena.coordination.redis_client import list_heartbeats
from matcharena.db.explain import summarize_execution_stats
from matcharena.db.indexes import describe_indexes

router = APIRouter(prefix="/api/ops", tags=["ops"])


@router.get("/indexes")
def indexes(container: Container = Depends(get_container)) -> dict:
    return {"indexes": describe_indexes(container.db)}


@router.get("/queue/stats")
def queue_stats(container: Container = Depends(get_container)) -> dict:
    return {
        "by_status": container.queue.count_by_status(),
        "players": container.players.count(),
    }


@router.get("/queue/explain")
def explain_queue_queries(
    lower: int = Query(default=700),
    upper: int = Query(default=1700),
    exclude_player_id: str = Query(default="none"),
    limit: int = Query(default=25, ge=1, le=500),
    container: Container = Depends(get_container),
) -> dict:
    candidates = container.queue.explain_find_candidates(lower, upper, exclude_player_id, limit)
    waiting = container.queue.explain_list_waiting(container.settings.worker_batch_size)
    return {
        "find_candidates": {
            "filter": {
                "status": "waiting",
                "rating": {"$gte": lower, "$lt": upper},
                "player_id": {"$ne": exclude_player_id},
            },
            "sort": {"created_at": 1},
            "limit": limit,
            "raw": candidates,
            "summary": summarize_execution_stats(candidates),
        },
        "list_waiting": {
            "filter": {"status": "waiting"},
            "sort": {"created_at": 1},
            "limit": container.settings.worker_batch_size,
            "raw": waiting,
            "summary": summarize_execution_stats(waiting),
        },
    }


@router.get("/workers")
def workers(container: Container = Depends(get_container)) -> dict:
    return {"workers": list_heartbeats(container.redis)}
