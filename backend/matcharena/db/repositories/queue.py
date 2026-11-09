from __future__ import annotations

from datetime import datetime
from typing import Iterable

from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.database import Database

from matcharena.db.mongo import QUEUE_ENTRIES
from matcharena.domain.models import ACTIVE_QUEUE_STATUSES, QueueEntry, QueueStatus


class QueueRepository:
    def __init__(self, db: Database) -> None:
        self._col = db[QUEUE_ENTRIES]

    def insert(self, entry: QueueEntry) -> QueueEntry:
        self._col.insert_one(entry.to_doc())
        return entry

    def get(self, queue_id: str) -> QueueEntry | None:
        doc = self._col.find_one({"_id": queue_id})
        return QueueEntry.from_doc(doc) if doc else None

    def find_active_for_player(self, player_id: str) -> QueueEntry | None:
        doc = self._col.find_one(
            {"player_id": player_id, "status": {"$in": list(ACTIVE_QUEUE_STATUSES)}},
            sort=[("created_at", ASCENDING)],
        )
        return QueueEntry.from_doc(doc) if doc else None

    def find_latest_for_player(self, player_id: str) -> QueueEntry | None:
        doc = self._col.find_one({"player_id": player_id}, sort=[("created_at", DESCENDING)])
        return QueueEntry.from_doc(doc) if doc else None

    def list_for_player(self, player_id: str, limit: int = 20) -> list[QueueEntry]:
        docs = self._col.find(
            {"player_id": player_id}, sort=[("created_at", DESCENDING)], limit=limit
        )
        return [QueueEntry.from_doc(d) for d in docs]

    def reactivate(self, queue_id: str, rating: int, now: datetime) -> QueueEntry | None:
        doc = self._col.find_one_and_update(
            {"_id": queue_id, "status": QueueStatus.CANCELLED.value},
            {
                "$set": {
                    "status": QueueStatus.WAITING.value,
                    "rating": rating,
                    "updated_at": now,
                    "match_id": None,
                    "reserved_by": None,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return QueueEntry.from_doc(doc) if doc else None

    def set_status(self, queue_id: str, status: QueueStatus, now: datetime) -> QueueEntry | None:
        doc = self._col.find_one_and_update(
            {"_id": queue_id},
            {"$set": {"status": status.value, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        return QueueEntry.from_doc(doc) if doc else None

    def list_waiting(self, limit: int) -> list[QueueEntry]:
        docs = self._col.find(
            {"status": QueueStatus.WAITING.value},
            sort=[("created_at", ASCENDING)],
            limit=limit,
        )
        return [QueueEntry.from_doc(d) for d in docs]

    def find_candidates(
        self, lower: int, upper: int, exclude_player_id: str, limit: int
    ) -> list[QueueEntry]:
        docs = self._col.find(
            {
                "status": QueueStatus.WAITING.value,
                "rating": {"$gte": lower, "$lt": upper},
                "player_id": {"$ne": exclude_player_id},
            },
            sort=[("created_at", ASCENDING)],
            limit=limit,
        )
        return [QueueEntry.from_doc(d) for d in docs]

    def reserve(self, queue_ids: Iterable[str], worker_id: str, now: datetime) -> int:
        result = self._col.update_many(
            {"_id": {"$in": list(queue_ids)}},
            {
                "$set": {
                    "status": QueueStatus.RESERVED.value,
                    "reserved_by": worker_id,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count

    def mark_matched(self, queue_ids: Iterable[str], match_id: str, now: datetime) -> int:
        result = self._col.update_many(
            {"_id": {"$in": list(queue_ids)}},
            {
                "$set": {
                    "status": QueueStatus.MATCHED.value,
                    "match_id": match_id,
                    "updated_at": now,
                }
            },
        )
        return result.modified_count

    def count_active_for_player(self, player_id: str) -> int:
        return self._col.count_documents(
            {"player_id": player_id, "status": {"$in": list(ACTIVE_QUEUE_STATUSES)}}
        )

    def count_by_status(self) -> dict[str, int]:
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        return {row["_id"]: row["count"] for row in self._col.aggregate(pipeline)}

    def explain_find_candidates(
        self, lower: int, upper: int, exclude_player_id: str, limit: int
    ) -> dict:
        cursor = self._col.find(
            {
                "status": QueueStatus.WAITING.value,
                "rating": {"$gte": lower, "$lt": upper},
                "player_id": {"$ne": exclude_player_id},
            },
        ).sort("created_at", ASCENDING).limit(limit)
        return cursor.explain("executionStats")

    def explain_list_waiting(self, limit: int) -> dict:
        cursor = self._col.find({"status": QueueStatus.WAITING.value}).sort(
            "created_at", ASCENDING
        ).limit(limit)
        return cursor.explain("executionStats")
