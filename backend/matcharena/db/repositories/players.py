from __future__ import annotations

from datetime import datetime
from typing import Iterable

from pymongo import ReturnDocument
from pymongo.database import Database

from matcharena.db.mongo import PLAYERS
from matcharena.domain.models import Player, PlayerStatus


class PlayerRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[PLAYERS]

    def insert(self, player: Player) -> Player:
        self._col.insert_one(player.to_doc())
        return player

    def get(self, player_id: str) -> Player | None:
        doc = self._col.find_one({"_id": player_id})
        return Player.from_doc(doc) if doc else None

    def get_by_username(self, username: str) -> Player | None:
        doc = self._col.find_one({"username": username})
        return Player.from_doc(doc) if doc else None

    def get_many(self, player_ids: Iterable[str]) -> list[Player]:
        ids = list(player_ids)
        docs = self._col.find({"_id": {"$in": ids}})
        by_id = {d["_id"]: Player.from_doc(d) for d in docs}
        return [by_id[i] for i in ids if i in by_id]

    def set_status(self, player_id: str, status: PlayerStatus, now: datetime) -> Player | None:
        doc = self._col.find_one_and_update(
            {"_id": player_id},
            {"$set": {"status": status.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return Player.from_doc(doc) if doc else None

    def set_status_many(self, player_ids: Iterable[str], status: PlayerStatus, now: datetime) -> int:
        result = self._col.update_many(
            {"_id": {"$in": list(player_ids)}},
            {"$set": {"status": status.value, "updated_at": now}},
        )
        return result.modified_count

    def set_rating(self, player_id: str, rating: int, now: datetime) -> Player | None:
        doc = self._col.find_one_and_update(
            {"_id": player_id},
            {"$set": {"rating": rating, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return Player.from_doc(doc) if doc else None

    def count(self) -> int:
        return self._col.estimated_document_count()
