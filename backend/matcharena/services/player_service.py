from __future__ import annotations

from dataclasses import dataclass

from matcharena.config import Settings
from matcharena.db.repositories import MatchRepository, PlayerRepository, QueueRepository
from matcharena.domain.clock import Clock
from matcharena.domain.errors import NotFound, ValidationFailed
from matcharena.domain.models import Match, Player, QueueEntry


@dataclass
class PlayerProfile:
    player: Player
    recent_queue_entries: list[QueueEntry]
    recent_matches: list[Match]


class PlayerService:
    def __init__(
        self,
        settings: Settings,
        players: PlayerRepository,
        queue: QueueRepository,
        matches: MatchRepository,
        clock: Clock,
    ) -> None:
        self._settings = settings
        self._players = players
        self._queue = queue
        self._matches = matches
        self._clock = clock

    def get(self, player_id: str) -> Player:
        player = self._players.get(player_id)
        if player is None:
            raise NotFound("Player not found", code="player_not_found")
        return player

    def profile(self, player_id: str) -> PlayerProfile:
        player = self.get(player_id)
        return PlayerProfile(
            player=player,
            recent_queue_entries=self._queue.list_for_player(player_id, limit=10),
            recent_matches=self._matches.list_for_player(player_id, limit=10),
        )

    def usernames(self, player_ids: list[str]) -> dict[str, str]:
        return {p.player_id: p.username for p in self._players.get_many(player_ids)}

    def update_rating(self, player_id: str, rating: int) -> Player:
        if not self._settings.min_rating <= rating <= self._settings.max_rating:
            raise ValidationFailed(
                f"Rating must be between {self._settings.min_rating} and {self._settings.max_rating}",
                code="rating_out_of_range",
            )
        player = self._players.set_rating(player_id, rating, self._clock.now())
        if player is None:
            raise NotFound("Player not found", code="player_not_found")
        return player
