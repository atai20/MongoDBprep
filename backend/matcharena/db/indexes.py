from __future__ import annotations

import logging

from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database

from matcharena.db.mongo import GAMES, MATCHES, PLAYERS, QUEUE_ENTRIES, SESSIONS

log = logging.getLogger(__name__)

INDEXES: dict[str, list[IndexModel]] = {
    PLAYERS: [
        IndexModel([("username", ASCENDING)], name="players_username_unique", unique=True),
        IndexModel([("rating", ASCENDING)], name="players_rating"),
    ],
    SESSIONS: [
        IndexModel([("token_hash", ASCENDING)], name="sessions_token_unique", unique=True),
        IndexModel([("expires_at", ASCENDING)], name="sessions_ttl", expireAfterSeconds=0),
    ],
    QUEUE_ENTRIES: [
        IndexModel([("player_id", ASCENDING), ("created_at", DESCENDING)], name="queue_player_recent"),
        IndexModel([("rating", ASCENDING), ("created_at", ASCENDING)], name="queue_rating_created"),
        IndexModel([("created_at", ASCENDING)], name="queue_created"),
    ],
    MATCHES: [
        IndexModel([("player_ids", ASCENDING), ("status", ASCENDING)], name="matches_player_status"),
        IndexModel([("created_at", DESCENDING)], name="matches_created"),
    ],
    GAMES: [
        IndexModel(
            [("match_id", ASCENDING)],
            name="games_match_unique",
            unique=True,
            partialFilterExpression={"match_id": {"$type": "string"}},
        ),
        IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="games_status_created"),
    ],
}


def ensure_indexes(db: Database) -> dict[str, list[str]]:
    created: dict[str, list[str]] = {}
    for collection, models in INDEXES.items():
        created[collection] = db[collection].create_indexes(models)
        log.info("indexes ensured", extra={"collection": collection, "indexes": created[collection]})
    return created


def describe_indexes(db: Database) -> dict[str, list[dict]]:
    return {name: list(db[name].list_indexes()) for name in INDEXES}
