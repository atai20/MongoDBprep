from __future__ import annotations

import argparse
import logging
import random
from datetime import timedelta

from matcharena.config import load_settings
from matcharena.container import build_container
from matcharena.db.indexes import ensure_indexes
from matcharena.db.mongo import QUEUE_ENTRIES
from matcharena.domain.clock import new_id
from matcharena.domain.models import Game, GameStatus, PlayerStatus, QueueStatus
from matcharena.logging_setup import configure_logging

log = logging.getLogger("matcharena.scripts.seed")

DEMO_USERS = [
    ("alice", 1200),
    ("bob", 1220),
    ("carol", 100),
    ("dave", 3000),
    ("erin", 2400),
    ("frank", 2420),
    ("gina", 1000),
    ("hugo", 1080),
    ("ivy", 1500),
    ("jude", 1510),
]


def seed_demo_players(container, password: str = "password123") -> dict[str, str]:
    ids: dict[str, str] = {}
    for username, rating in DEMO_USERS:
        existing = container.players.get_by_username(username)
        if existing is not None:
            container.players.set_rating(existing.player_id, rating, container.clock.now())
            container.players.set_status(existing.player_id, PlayerStatus.IDLE, container.clock.now())
            ids[username] = existing.player_id
            continue
        player, _token = container.auth.register(username, password, rating)
        ids[username] = player.player_id
    return ids


def seed_lobbies(container, host_id: str) -> None:
    now = container.clock.now()
    if container.games.list_open_lobbies(limit=1):
        return
    container.games.insert(
        Game(
            game_id=new_id(),
            match_id=None,
            capacity=4,
            status=GameStatus.OPEN,
            created_at=now,
            player_ids=[host_id],
            host_id=host_id,
            name="Open Arena",
        )
    )
    container.games.insert(
        Game(
            game_id=new_id(),
            match_id=None,
            capacity=2,
            status=GameStatus.OPEN,
            created_at=now,
            player_ids=[host_id],
            host_id=host_id,
            name="Duel Pit",
        )
    )


def seed_queue_volume(db, count: int, rng: random.Random) -> None:
    now_clock = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    statuses = (
        [QueueStatus.CANCELLED.value] * 6
        + [QueueStatus.MATCHED.value] * 3
        + [QueueStatus.WAITING.value] * 1
    )
    docs = []
    for i in range(count):
        created = now_clock - timedelta(seconds=rng.randint(0, 86_400))
        status = statuses[i % len(statuses)]
        docs.append(
            {
                "_id": new_id(),
                "player_id": f"seed-{i:05d}",
                "rating": rng.randint(100, 3000),
                "status": status,
                "created_at": created,
                "updated_at": created,
                "match_id": new_id() if status == QueueStatus.MATCHED.value else None,
                "reserved_by": None,
            }
        )
        if len(docs) >= 500:
            db[QUEUE_ENTRIES].insert_many(docs)
            docs = []
    if docs:
        db[QUEUE_ENTRIES].insert_many(docs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed MatchArena demo data")
    parser.add_argument("--queue-volume", type=int, default=8000)
    parser.add_argument("--reset-volume", action="store_true")
    args = parser.parse_args()

    configure_logging()
    settings = load_settings()
    container = build_container(settings)
    ensure_indexes(container.db)

    ids = seed_demo_players(container)
    seed_lobbies(container, ids["ivy"])

    if args.reset_volume:
        container.db[QUEUE_ENTRIES].delete_many({"player_id": {"$regex": "^seed-"}})
    existing_seed = container.db[QUEUE_ENTRIES].count_documents({"player_id": {"$regex": "^seed-"}})
    if existing_seed < args.queue_volume:
        seed_queue_volume(container.db, args.queue_volume - existing_seed, random.Random(42))

    log.info(
        "seed complete",
        extra={
            "players": container.players.count(),
            "queue": container.queue.count_by_status(),
        },
    )
    print("demo users: " + ", ".join(f"{u}/{r}" for u, r in DEMO_USERS))
    print("password: password123")


if __name__ == "__main__":
    main()
