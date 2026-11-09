from __future__ import annotations

import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return truncate_to_millis(datetime.now(timezone.utc))


class ManualClock:
    """Deterministic clock for scripts, simulations and tests."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = truncate_to_millis(start or datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc))
        self._lock = threading.Lock()

    def now(self) -> datetime:
        with self._lock:
            return self._now

    def advance(self, seconds: float) -> datetime:
        with self._lock:
            self._now = truncate_to_millis(self._now + timedelta(seconds=seconds))
            return self._now


def truncate_to_millis(value: datetime) -> datetime:
    # MongoDB stores dates with millisecond precision.
    return value.replace(microsecond=(value.microsecond // 1000) * 1000)


def new_id() -> str:
    return uuid.uuid4().hex
