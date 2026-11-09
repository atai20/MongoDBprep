from __future__ import annotations

from datetime import datetime

from pymongo import DESCENDING, ReturnDocument
from pymongo.database import Database

from matcharena.db.mongo import GAMES
from matcharena.domain.models import Game, GameStatus


class GameRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[GAMES]

    def insert(self, game: Game) -> Game:
        self._col.insert_one(game.to_doc())
        return game

    def get(self, game_id: str) -> Game | None:
        doc = self._col.find_one({"_id": game_id})
        return Game.from_doc(doc) if doc else None

    def get_by_match(self, match_id: str) -> Game | None:
        doc = self._col.find_one({"match_id": match_id})
        return Game.from_doc(doc) if doc else None

    def list_open_lobbies(self, limit: int = 50) -> list[Game]:
        docs = self._col.find(
            {"status": GameStatus.OPEN.value, "match_id": {"$exists": False}},
            sort=[("created_at", DESCENDING)],
            limit=limit,
        )
        return [Game.from_doc(d) for d in docs]

    def add_player(self, game_id: str, player_id: str, now: datetime) -> Game | None:
        doc = self._col.find_one_and_update(
            {"_id": game_id},
            {"$push": {"player_ids": player_id}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return Game.from_doc(doc) if doc else None

    def remove_player(self, game_id: str, player_id: str, now: datetime) -> Game | None:
        doc = self._col.find_one_and_update(
            {"_id": game_id},
            {"$pull": {"player_ids": player_id}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return Game.from_doc(doc) if doc else None

    def set_status(self, game_id: str, status: GameStatus, now: datetime) -> Game | None:
        doc = self._col.find_one_and_update(
            {"_id": game_id},
            {"$set": {"status": status.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return Game.from_doc(doc) if doc else None
