from __future__ import annotations

import logging
from dataclasses import dataclass

from matcharena.config import Settings
from matcharena.db.repositories import GameRepository, MatchRepository, PlayerRepository, QueueRepository
from matcharena.domain import elo
from matcharena.domain.clock import Clock, new_id
from matcharena.domain.errors import Conflict, NotFound
from matcharena.domain.models import (
    Game,
    Match,
    Player,
    PlayerStatus,
    QueueEntry,
    QueueStatus,
)

log = logging.getLogger(__name__)


@dataclass
class EnqueueResult:
    entry: QueueEntry
    created: bool


@dataclass
class QueueStatusView:
    state: str
    entry: QueueEntry | None
    wait_seconds: float | None
    tolerance: int | None
    window: elo.RatingWindow | None
    match: Match | None


@dataclass
class CurrentMatchView:
    match: Match
    game: Game | None
    players: list[Player]


class MatchmakingService:
    def __init__(
        self,
        settings: Settings,
        players: PlayerRepository,
        queue: QueueRepository,
        matches: MatchRepository,
        games: GameRepository,
        clock: Clock,
    ) -> None:
        self._settings = settings
        self._players = players
        self._queue = queue
        self._matches = matches
        self._games = games
        self._clock = clock
        self.before_insert = None

    def enqueue(self, player_id: str) -> EnqueueResult:
        player = self._require_player(player_id)
        if player.status in (PlayerStatus.MATCHED, PlayerStatus.IN_GAME):
            if self._matches.find_current_for_player(player_id) is not None:
                raise Conflict("Player already has an active match", code="already_matched")

        existing = self._queue.find_active_for_player(player_id)
        if existing is not None:
            return EnqueueResult(entry=existing, created=False)

        if self.before_insert is not None:
            self.before_insert()

        now = self._clock.now()
        entry = self._reuse_cancelled_entry(player, now)
        if entry is None:
            entry = self._queue.insert(
                QueueEntry(
                    queue_id=new_id(),
                    player_id=player_id,
                    rating=player.rating,
                    status=QueueStatus.WAITING,
                    created_at=now,
                    updated_at=now,
                )
            )
        self._players.set_status(player_id, PlayerStatus.QUEUED, now)
        log.info("player queued", extra={"player_id": player_id, "queue_id": entry.queue_id})
        return EnqueueResult(entry=entry, created=True)

    def cancel(self, player_id: str) -> QueueEntry:
        entry = self._queue.find_active_for_player(player_id)
        if entry is None:
            raise NotFound("Player is not in the matchmaking queue", code="not_queued")
        now = self._clock.now()
        cancelled = self._queue.set_status(entry.queue_id, QueueStatus.CANCELLED, now)
        self._players.set_status(player_id, PlayerStatus.IDLE, now)
        log.info("queue entry cancelled", extra={"player_id": player_id, "queue_id": entry.queue_id})
        return cancelled or entry

    def status(self, player_id: str) -> QueueStatusView:
        player = self._require_player(player_id)
        entry = self._queue.find_active_for_player(player_id)
        match = self._matches.find_current_for_player(player_id)
        if entry is not None:
            now = self._clock.now()
            waited = max(0.0, (now - entry.updated_at).total_seconds())
            tolerance = elo.tolerance_for_wait(waited, self._settings)
            return QueueStatusView(
                state=entry.status.value,
                entry=entry,
                wait_seconds=round(waited, 1),
                tolerance=tolerance,
                window=elo.rating_window(entry.rating, tolerance, self._settings),
                match=match,
            )
        if match is not None:
            state = "in_game" if player.status == PlayerStatus.IN_GAME else "matched"
            return QueueStatusView(state, None, None, None, None, match)
        return QueueStatusView("idle", None, None, None, None, None)

    def current_match(self, player_id: str) -> CurrentMatchView | None:
        match = self._matches.find_current_for_player(player_id)
        if match is None:
            return None
        return CurrentMatchView(
            match=match,
            game=self._games.get(match.game_id),
            players=self._players.get_many(match.player_ids),
        )

    def _reuse_cancelled_entry(self, player: Player, now) -> QueueEntry | None:
        latest = self._queue.find_latest_for_player(player.player_id)
        if latest is None or latest.status != QueueStatus.CANCELLED:
            return None
        return self._queue.reactivate(latest.queue_id, player.rating, now)

    def _require_player(self, player_id: str) -> Player:
        player = self._players.get(player_id)
        if player is None:
            raise NotFound("Player not found", code="player_not_found")
        return player
