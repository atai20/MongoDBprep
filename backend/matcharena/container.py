from __future__ import annotations

from dataclasses import dataclass

import redis
from pymongo.database import Database

from matcharena.config import Settings, load_settings
from matcharena.coordination.lock import LockFactory
from matcharena.coordination.redis_client import get_redis
from matcharena.db.mongo import get_database
from matcharena.db.repositories import (
    GameRepository,
    MatchRepository,
    PlayerRepository,
    QueueRepository,
    SessionRepository,
)
from matcharena.domain.clock import Clock, SystemClock
from matcharena.services.auth_service import AuthService
from matcharena.services.game_service import GameService
from matcharena.services.matchmaking_service import MatchmakingService
from matcharena.services.player_service import PlayerService
from matcharena.workers.matchmaker import MatchmakingWorker


@dataclass
class Container:
    settings: Settings
    db: Database
    redis: redis.Redis
    clock: Clock
    players: PlayerRepository
    sessions: SessionRepository
    queue: QueueRepository
    matches: MatchRepository
    games: GameRepository
    auth: AuthService
    player_service: PlayerService
    matchmaking: MatchmakingService
    game_service: GameService

    def lock_factory(self) -> LockFactory:
        return LockFactory(self.redis, self.settings.lock_key, self.settings.lock_ttl_ms)

    def worker(self, worker_id: str | None = None) -> MatchmakingWorker:
        return MatchmakingWorker(
            settings=self.settings,
            queue=self.queue,
            matches=self.matches,
            games=self.games,
            players=self.players,
            lock_factory=self.lock_factory(),
            clock=self.clock,
            worker_id=worker_id,
        )


def build_container(
    settings: Settings | None = None,
    *,
    db: Database | None = None,
    redis_client: redis.Redis | None = None,
    clock: Clock | None = None,
) -> Container:
    settings = settings or load_settings()
    db = db if db is not None else get_database(settings)
    redis_client = redis_client if redis_client is not None else get_redis(settings)
    clock = clock or SystemClock()

    players = PlayerRepository(db)
    sessions = SessionRepository(db)
    queue = QueueRepository(db)
    matches = MatchRepository(db)
    games = GameRepository(db)

    return Container(
        settings=settings,
        db=db,
        redis=redis_client,
        clock=clock,
        players=players,
        sessions=sessions,
        queue=queue,
        matches=matches,
        games=games,
        auth=AuthService(settings, players, sessions, clock),
        player_service=PlayerService(settings, players, queue, matches, clock),
        matchmaking=MatchmakingService(settings, players, queue, matches, games, clock),
        game_service=GameService(settings, players, matches, games, clock),
    )
