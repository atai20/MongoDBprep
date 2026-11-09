from __future__ import annotations

import logging

from matcharena.config import Settings
from matcharena.db.repositories import GameRepository, MatchRepository, PlayerRepository
from matcharena.domain.clock import Clock, new_id
from matcharena.domain.errors import Conflict, Forbidden, NotFound, ValidationFailed
from matcharena.domain.models import (
    CURRENT_MATCH_STATUSES,
    Game,
    GameStatus,
    MatchStatus,
    PlayerStatus,
)

log = logging.getLogger(__name__)


class GameService:
    def __init__(
        self,
        settings: Settings,
        players: PlayerRepository,
        matches: MatchRepository,
        games: GameRepository,
        clock: Clock,
    ) -> None:
        self._settings = settings
        self._players = players
        self._matches = matches
        self._games = games
        self._clock = clock
        self.before_join_write = None

    def get(self, game_id: str) -> Game:
        game = self._games.get(game_id)
        if game is None:
            raise NotFound("Game not found", code="game_not_found")
        return game

    def list_open_lobbies(self) -> list[Game]:
        return self._games.list_open_lobbies()

    def create_lobby(self, host_id: str, name: str, capacity: int) -> Game:
        if not self._settings.game_min_capacity <= capacity <= self._settings.game_max_capacity:
            raise ValidationFailed("Unsupported lobby capacity", code="invalid_capacity")
        now = self._clock.now()
        game = self._games.insert(
            Game(
                game_id=new_id(),
                match_id=None,
                capacity=capacity,
                status=GameStatus.OPEN,
                created_at=now,
                host_id=host_id,
                name=name,
            )
        )
        return self.join(game.game_id, host_id)

    def join(self, game_id: str, player_id: str) -> Game:
        player = self._players.get(player_id)
        if player is None:
            raise NotFound("Player not found", code="player_not_found")
        game = self.get(game_id)
        if game.status == GameStatus.CLOSED:
            raise Conflict("Game is closed", code="game_closed")

        match = None
        if game.match_id is not None:
            match = self._matches.get(game.match_id)
            if match is None or player_id not in match.player_ids:
                raise Forbidden("Player is not assigned to this game", code="not_assigned")
            if match.status.value not in CURRENT_MATCH_STATUSES:
                raise Conflict("Match is no longer active", code="match_closed")
        elif player.status == PlayerStatus.QUEUED:
            raise Conflict("Leave matchmaking before joining a lobby", code="player_queued")

        if player_id in game.player_ids:
            return game
        if player.status == PlayerStatus.IN_GAME:
            raise Conflict("Player is already in another game", code="already_in_game")
        if len(game.player_ids) >= game.capacity:
            raise Conflict("Game is full", code="game_full")

        if self.before_join_write is not None:
            self.before_join_write(game)

        now = self._clock.now()
        updated = self._games.add_player(game_id, player_id, now)
        if updated is None:
            raise NotFound("Game not found", code="game_not_found")
        if len(updated.player_ids) >= updated.capacity and updated.status == GameStatus.OPEN:
            updated = self._games.set_status(game_id, GameStatus.FULL, now) or updated
            if match is not None:
                self._matches.set_status(match.match_id, MatchStatus.ACTIVE)
        self._players.set_status(player_id, PlayerStatus.IN_GAME, now)
        log.info("player joined game", extra={"player_id": player_id, "game_id": game_id})
        return updated

    def leave(self, game_id: str, player_id: str) -> Game:
        game = self.get(game_id)
        if player_id not in game.player_ids:
            raise Conflict("Player is not in this game", code="not_in_game")
        now = self._clock.now()
        updated = self._games.remove_player(game_id, player_id, now) or game
        self._players.set_status(player_id, PlayerStatus.IDLE, now)

        if game.match_id is not None:
            match = self._matches.set_status(game.match_id, MatchStatus.ABANDONED)
            updated = self._games.set_status(game_id, GameStatus.CLOSED, now) or updated
            if match is not None:
                self._players.set_status_many(match.player_ids, PlayerStatus.IDLE, now)
        elif not updated.player_ids:
            updated = self._games.set_status(game_id, GameStatus.CLOSED, now) or updated
        elif updated.status == GameStatus.FULL:
            updated = self._games.set_status(game_id, GameStatus.OPEN, now) or updated
        log.info("player left game", extra={"player_id": player_id, "game_id": game_id})
        return updated
