from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from pymongo.errors import DuplicateKeyError

from matcharena.config import Settings
from matcharena.db.repositories import PlayerRepository, SessionRepository
from matcharena.domain.clock import Clock, new_id
from matcharena.domain.errors import Conflict, Unauthorized
from matcharena.domain.models import Player, PlayerStatus

PBKDF2_ITERATIONS = 120_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, iterations, salt, expected = encoded.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
    return hmac.compare_digest(digest.hex(), expected)


class AuthService:
    def __init__(
        self, settings: Settings, players: PlayerRepository, sessions: SessionRepository, clock: Clock
    ) -> None:
        self._settings = settings
        self._players = players
        self._sessions = sessions
        self._clock = clock

    def register(self, username: str, password: str, rating: int | None = None) -> tuple[Player, str]:
        now = self._clock.now()
        player = Player(
            player_id=new_id(),
            username=username,
            rating=rating if rating is not None else self._settings.default_rating,
            status=PlayerStatus.IDLE,
            created_at=now,
            updated_at=now,
            password_hash=hash_password(password),
        )
        try:
            self._players.insert(player)
        except DuplicateKeyError:
            raise Conflict("Username is already taken", code="username_taken") from None
        return player, self._issue_token(player)

    def login(self, username: str, password: str) -> tuple[Player, str]:
        player = self._players.get_by_username(username)
        if player is None or not verify_password(password, player.password_hash):
            raise Unauthorized("Invalid username or password", code="invalid_credentials")
        return player, self._issue_token(player)

    def authenticate(self, token: str) -> Player:
        player_id = self._sessions.resolve(token, self._clock.now())
        if player_id is None:
            raise Unauthorized("Session expired or invalid", code="invalid_session")
        player = self._players.get(player_id)
        if player is None:
            raise Unauthorized("Session expired or invalid", code="invalid_session")
        return player

    def logout(self, token: str) -> None:
        self._sessions.revoke(token)

    def _issue_token(self, player: Player) -> str:
        token = secrets.token_urlsafe(32)
        now = self._clock.now()
        self._sessions.create(token, player.player_id, now, now + timedelta(hours=self._settings.session_ttl_hours))
        return token
