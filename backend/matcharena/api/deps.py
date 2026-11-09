from __future__ import annotations

from fastapi import Depends, Header, Request

from matcharena.container import Container
from matcharena.domain.errors import Unauthorized
from matcharena.domain.models import Player


def get_container(request: Request) -> Container:
    return request.app.state.container


def _parse_bearer(authorization: str | None) -> str:
    if not authorization:
        raise Unauthorized("Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise Unauthorized("Authorization header must be a Bearer token")
    return token.strip()


def get_current_player(
    authorization: str | None = Header(default=None),
    container: Container = Depends(get_container),
) -> Player:
    return container.auth.authenticate(_parse_bearer(authorization))


def get_optional_token(authorization: str | None = Header(default=None)) -> str | None:
    if not authorization:
        return None
    try:
        return _parse_bearer(authorization)
    except Unauthorized:
        return None
