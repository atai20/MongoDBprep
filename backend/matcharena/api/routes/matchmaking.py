from __future__ import annotations

from fastapi import APIRouter, Depends, status

from matcharena.api import serializers
from matcharena.api.deps import get_container, get_current_player
from matcharena.container import Container
from matcharena.domain.errors import NotFound
from matcharena.domain.models import Player

router = APIRouter(prefix="/api/matchmaking", tags=["matchmaking"])


@router.post("/queue", status_code=status.HTTP_200_OK)
def enqueue(
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    result = container.matchmaking.enqueue(player.player_id)
    return {
        "created": result.created,
        "entry": serializers.queue_entry(result.entry),
    }


@router.delete("/queue")
def cancel(
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    entry = container.matchmaking.cancel(player.player_id)
    return {"entry": serializers.queue_entry(entry)}


@router.get("/status")
def status_view(
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    return serializers.queue_status(container.matchmaking.status(player.player_id))


@router.get("/current")
def current_match(
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    view = container.matchmaking.current_match(player.player_id)
    if view is None:
        raise NotFound("No current match", code="no_current_match")
    return serializers.current_match(view)
