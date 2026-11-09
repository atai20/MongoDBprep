from __future__ import annotations

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database

from matcharena.config import Settings

PLAYERS = "players"
SESSIONS = "sessions"
QUEUE_ENTRIES = "queue_entries"
MATCHES = "matches"
GAMES = "games"


@lru_cache(maxsize=8)
def _client(uri: str) -> MongoClient:
    return MongoClient(
        uri,
        tz_aware=True,
        serverSelectionTimeoutMS=3000,
        maxPoolSize=50,
        appname="matcharena",
    )


def get_client(settings: Settings) -> MongoClient:
    return _client(settings.mongo_uri)


def get_database(settings: Settings) -> Database:
    return get_client(settings)[settings.mongo_db]


def ping(db: Database) -> bool:
    try:
        db.client.admin.command("ping")
        return True
    except Exception:
        return False
