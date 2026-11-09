from __future__ import annotations

from fastapi import APIRouter, Depends

from matcharena.api import serializers
from matcharena.api.deps import get_container, get_current_player
from matcharena.container import Container
from matcharena.domain.models import Player
from matcharena.validation.schemas import RatingUpdateRequest

router = APIRouter(prefix="/api", tags=["players"])


@router.get("/me")
def me(
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    return serializers.profile(container.player_service.profile(player.player_id))


@router.patch("/me/rating")
def update_rating(
    body: RatingUpdateRequest,
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    updated = container.player_service.update_rating(player.player_id, body.rating)
    return serializers.player_public(updated)
