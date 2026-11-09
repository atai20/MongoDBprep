from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from matcharena.api import serializers
from matcharena.api.deps import get_container, get_optional_token
from matcharena.container import Container
from matcharena.domain.errors import ValidationFailed
from matcharena.validation.schemas import LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, container: Container = Depends(get_container)) -> dict:
    settings = container.settings
    if body.rating is not None and not settings.min_rating <= body.rating <= settings.max_rating:
        raise ValidationFailed(
            f"Rating must be between {settings.min_rating} and {settings.max_rating}",
            code="rating_out_of_range",
        )
    player, token = container.auth.register(body.username, body.password, body.rating)
    return serializers.player_private(player, token)


@router.post("/login")
def login(body: LoginRequest, container: Container = Depends(get_container)) -> dict:
    player, token = container.auth.login(body.username, body.password)
    return serializers.player_private(player, token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str | None = Depends(get_optional_token),
    container: Container = Depends(get_container),
) -> Response:
    if token:
        container.auth.logout(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
