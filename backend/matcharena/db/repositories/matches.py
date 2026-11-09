from __future__ import annotations

from pymongo import DESCENDING, ReturnDocument
from pymongo.database import Database

from matcharena.db.mongo import MATCHES
from matcharena.domain.models import CURRENT_MATCH_STATUSES, Match, MatchStatus


class MatchRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[MATCHES]

    def insert(self, match: Match) -> Match:
        self._col.insert_one(match.to_doc())
        return match

    def get(self, match_id: str) -> Match | None:
        doc = self._col.find_one({"_id": match_id})
        return Match.from_doc(doc) if doc else None

    def find_current_for_player(self, player_id: str) -> Match | None:
        doc = self._col.find_one(
            {"player_ids": player_id, "status": {"$in": list(CURRENT_MATCH_STATUSES)}},
            sort=[("created_at", DESCENDING)],
        )
        return Match.from_doc(doc) if doc else None

    def list_for_player(self, player_id: str, limit: int = 20) -> list[Match]:
        docs = self._col.find(
            {"player_ids": player_id}, sort=[("created_at", DESCENDING)], limit=limit
        )
        return [Match.from_doc(d) for d in docs]

    def count_current_for_player(self, player_id: str) -> int:
        return self._col.count_documents(
            {"player_ids": player_id, "status": {"$in": list(CURRENT_MATCH_STATUSES)}}
        )

    def set_status(self, match_id: str, status: MatchStatus) -> Match | None:
        doc = self._col.find_one_and_update(
            {"_id": match_id},
            {"$set": {"status": status.value}},
            return_document=ReturnDocument.AFTER,
        )
        return Match.from_doc(doc) if doc else None
