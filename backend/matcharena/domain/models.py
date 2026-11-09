from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PlayerStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    MATCHED = "matched"
    IN_GAME = "in_game"


class QueueStatus(str, Enum):
    WAITING = "waiting"
    RESERVED = "reserved"
    MATCHED = "matched"
    CANCELLED = "cancelled"


ACTIVE_QUEUE_STATUSES = (QueueStatus.WAITING.value, QueueStatus.RESERVED.value)


class MatchStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


CURRENT_MATCH_STATUSES = (MatchStatus.PENDING.value, MatchStatus.ACTIVE.value)


class GameStatus(str, Enum):
    OPEN = "open"
    FULL = "full"
    CLOSED = "closed"


@dataclass
class Player:
    player_id: str
    username: str
    rating: int
    status: PlayerStatus
    created_at: datetime
    updated_at: datetime
    password_hash: str = ""

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "Player":
        return cls(
            player_id=doc["_id"],
            username=doc["username"],
            rating=int(doc["rating"]),
            status=PlayerStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            password_hash=doc.get("password_hash", ""),
        )

    def to_doc(self) -> dict[str, Any]:
        return {
            "_id": self.player_id,
            "username": self.username,
            "rating": self.rating,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "password_hash": self.password_hash,
        }


@dataclass
class QueueEntry:
    queue_id: str
    player_id: str
    rating: int
    status: QueueStatus
    created_at: datetime
    updated_at: datetime
    match_id: str | None = None
    reserved_by: str | None = None

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "QueueEntry":
        return cls(
            queue_id=doc["_id"],
            player_id=doc["player_id"],
            rating=int(doc["rating"]),
            status=QueueStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            match_id=doc.get("match_id"),
            reserved_by=doc.get("reserved_by"),
        )

    def to_doc(self) -> dict[str, Any]:
        return {
            "_id": self.queue_id,
            "player_id": self.player_id,
            "rating": self.rating,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "match_id": self.match_id,
            "reserved_by": self.reserved_by,
        }


@dataclass
class Match:
    match_id: str
    player_ids: list[str]
    status: MatchStatus
    created_at: datetime
    game_id: str
    rating_spread: int = 0

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "Match":
        return cls(
            match_id=doc["_id"],
            player_ids=list(doc["player_ids"]),
            status=MatchStatus(doc["status"]),
            created_at=doc["created_at"],
            game_id=doc["game_id"],
            rating_spread=int(doc.get("rating_spread", 0)),
        )

    def to_doc(self) -> dict[str, Any]:
        return {
            "_id": self.match_id,
            "player_ids": self.player_ids,
            "status": self.status.value,
            "created_at": self.created_at,
            "game_id": self.game_id,
            "rating_spread": self.rating_spread,
        }


@dataclass
class Game:
    game_id: str
    match_id: str | None
    capacity: int
    status: GameStatus
    created_at: datetime
    player_ids: list[str] = field(default_factory=list)
    host_id: str | None = None
    name: str | None = None

    @property
    def is_lobby(self) -> bool:
        return self.match_id is None

    @classmethod
    def from_doc(cls, doc: dict[str, Any]) -> "Game":
        return cls(
            game_id=doc["_id"],
            match_id=doc.get("match_id"),
            capacity=int(doc["capacity"]),
            status=GameStatus(doc["status"]),
            created_at=doc["created_at"],
            player_ids=list(doc.get("player_ids", [])),
            host_id=doc.get("host_id"),
            name=doc.get("name"),
        )

    def to_doc(self) -> dict[str, Any]:
        doc: dict[str, Any] = {
            "_id": self.game_id,
            "capacity": self.capacity,
            "status": self.status.value,
            "created_at": self.created_at,
            "player_ids": self.player_ids,
            "host_id": self.host_id,
            "name": self.name,
        }
        if self.match_id is not None:
            doc["match_id"] = self.match_id
        return doc
