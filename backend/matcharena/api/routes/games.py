from __future__ import annotations

from fastapi import APIRouter, Depends, status

from matcharena.api import serializers
from matcharena.api.deps import get_container, get_current_player
from matcharena.container import Container
from matcharena.domain.models import Player
from matcharena.validation.schemas import CreateLobbyRequest

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/")
def list_games(container: Container = Depends(get_container)) -> dict:
    return {"games": [serializers.game_public(g) for g in container.game_service.list_open_lobbies()]}


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_lobby(
    body: CreateLobbyRequest,
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    game = container.game_service.create_lobby(player.player_id, body.name, body.capacity)
    return serializers.game_public(game)


@router.get("/{game_id}")
def get_game(game_id: str, container: Container = Depends(get_container)) -> dict:
    return serializers.game_public(container.game_service.get(game_id))


@router.post("/{game_id}/join")
def join_game(
    game_id: str,
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    return serializers.game_public(container.game_service.join(game_id, player.player_id))


@router.post("/{game_id}/leave")
def leave_game(
    game_id: str,
    player: Player = Depends(get_current_player),
    container: Container = Depends(get_container),
) -> dict:
    return serializers.game_public(container.game_service.leave(game_id, player.player_id))
