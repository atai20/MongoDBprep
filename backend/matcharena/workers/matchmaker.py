from __future__ import annotations

import logging
import os
import socket
import threading
from dataclasses import dataclass, field
from typing import Callable

from pymongo.errors import PyMongoError

from matcharena.config import Settings
from matcharena.coordination.lock import RedisLock
from matcharena.db.repositories import GameRepository, MatchRepository, PlayerRepository, QueueRepository
from matcharena.domain import elo
from matcharena.domain.clock import Clock, new_id
from matcharena.domain.models import Game, GameStatus, Match, MatchStatus, PlayerStatus, QueueEntry

log = logging.getLogger(__name__)


def default_worker_id() -> str:
    return f"{socket.gethostname()}-{os.getpid()}-{new_id()[:6]}"


@dataclass
class CycleResult:
    worker_id: str
    skipped: bool = False
    scanned: int = 0
    matches: list[Match] = field(default_factory=list)
    errors: int = 0


class MatchmakingWorker:
    def __init__(
        self,
        settings: Settings,
        queue: QueueRepository,
        matches: MatchRepository,
        games: GameRepository,
        players: PlayerRepository,
        lock_factory: Callable[[], RedisLock],
        clock: Clock,
        worker_id: str | None = None,
        on_cycle: Callable[[CycleResult], None] | None = None,
    ) -> None:
        self.settings = settings
        self.queue = queue
        self.matches = matches
        self.games = games
        self.players = players
        self.lock_factory = lock_factory
        self.clock = clock
        self.worker_id = worker_id or default_worker_id()
        self.on_cycle = on_cycle
        self.after_scan = None
        self.before_reserve = None

    def run_forever(self, stop: threading.Event) -> None:
        log.info("matchmaking worker started", extra={"worker_id": self.worker_id})
        while not stop.is_set():
            try:
                result = self.run_once()
                if self.on_cycle:
                    self.on_cycle(result)
                if result.matches:
                    log.info(
                        "cycle created matches",
                        extra={"worker_id": self.worker_id, "count": len(result.matches)},
                    )
            except Exception:
                log.exception("matchmaking cycle crashed", extra={"worker_id": self.worker_id})
            stop.wait(self.settings.worker_poll_interval_seconds)
        log.info("matchmaking worker stopped", extra={"worker_id": self.worker_id})

    def run_once(self) -> CycleResult:
        lock = self.lock_factory()
        if not lock.acquire():
            return CycleResult(worker_id=self.worker_id, skipped=True)
        try:
            return self.run_cycle()
        finally:
            lock.release()

    def run_cycle(self) -> CycleResult:
        now = self.clock.now()
        result = CycleResult(worker_id=self.worker_id)
        waiting = self.queue.list_waiting(limit=self.settings.worker_batch_size)
        result.scanned = len(waiting)
        if self.after_scan is not None:
            self.after_scan(waiting)
        claimed: set[str] = set()

        for anchor in waiting:
            if anchor.queue_id in claimed:
                continue
            opponent = self._find_opponent(anchor, claimed, now)
            if opponent is None:
                continue
            match = self._create_match(anchor, opponent, now)
            if match is None:
                result.errors += 1
                continue
            claimed.update({anchor.queue_id, opponent.queue_id})
            result.matches.append(match)
        return result

    def _find_opponent(self, anchor: QueueEntry, claimed: set[str], now) -> QueueEntry | None:
        tolerance = elo.current_tolerance(anchor, now, self.settings)
        window = elo.rating_window(anchor.rating, tolerance, self.settings)
        if window.lower > window.upper:
            return None
        candidates = self.queue.find_candidates(
            window.lower,
            window.upper,
            exclude_player_id=anchor.player_id,
            limit=self.settings.candidate_limit,
        )
        return elo.choose_opponent(anchor, candidates, now, self.settings, exclude=claimed)

    def _create_match(self, a: QueueEntry, b: QueueEntry, now) -> Match | None:
        entry_ids = [a.queue_id, b.queue_id]
        if self.before_reserve is not None:
            self.before_reserve(a, b)
        self.queue.reserve(entry_ids, self.worker_id, now)
        try:
            match_id = new_id()
            game_id = new_id()
            match = Match(
                match_id=match_id,
                player_ids=[a.player_id, b.player_id],
                status=MatchStatus.PENDING,
                created_at=now,
                game_id=game_id,
                rating_spread=abs(a.rating - b.rating),
            )
            self.games.insert(
                Game(
                    game_id=game_id,
                    match_id=match_id,
                    capacity=self.settings.match_size,
                    status=GameStatus.OPEN,
                    created_at=now,
                )
            )
            self.matches.insert(match)
            self.queue.mark_matched(entry_ids, match_id, now)
            self.players.set_status_many(match.player_ids, PlayerStatus.MATCHED, now)
        except PyMongoError:
            log.exception(
                "failed to create match",
                extra={"worker_id": self.worker_id, "queue_ids": entry_ids},
            )
            return None
        log.info(
            "match created",
            extra={"worker_id": self.worker_id, "match_id": match_id, "players": match.player_ids},
        )
        return match
