from __future__ import annotations

import hashlib
from datetime import datetime

from pymongo.database import Database

from matcharena.db.mongo import SESSIONS


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class SessionRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[SESSIONS]

    def create(self, token: str, player_id: str, now: datetime, expires_at: datetime) -> None:
        self._col.insert_one(
            {
                "token_hash": hash_token(token),
                "player_id": player_id,
                "created_at": now,
                "expires_at": expires_at,
            }
        )

    def resolve(self, token: str, now: datetime) -> str | None:
        doc = self._col.find_one({"token_hash": hash_token(token), "expires_at": {"$gt": now}})
        return doc["player_id"] if doc else None

    def revoke(self, token: str) -> None:
        self._col.delete_one({"token_hash": hash_token(token)})
