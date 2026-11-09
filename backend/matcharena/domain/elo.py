from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from matcharena.config import Settings
from matcharena.domain.models import QueueEntry


@dataclass(frozen=True)
class RatingWindow:
    lower: int
    upper: int

    def contains(self, rating: int) -> bool:
        return self.lower <= rating <= self.upper


def seconds_waited(entry: QueueEntry, now: datetime) -> float:
    return max(0.0, (now - entry.created_at).total_seconds())


def tolerance_for_wait(wait_seconds: float, settings: Settings) -> int:
    steps = int(max(0.0, wait_seconds) // settings.tolerance_interval_seconds)
    tolerance = settings.base_tolerance + steps * settings.tolerance_step
    return min(tolerance, settings.max_tolerance)


def current_tolerance(entry: QueueEntry, now: datetime, settings: Settings) -> int:
    return tolerance_for_wait(seconds_waited(entry, now), settings)


def rating_window(rating: int, tolerance: int, settings: Settings) -> RatingWindow:
    lower = max(rating - tolerance, settings.min_rating + tolerance)
    upper = min(rating + tolerance, settings.max_rating - tolerance)
    return RatingWindow(lower=lower, upper=upper)


def is_compatible(a: QueueEntry, b: QueueEntry, now: datetime, settings: Settings) -> bool:
    if a.player_id == b.player_id:
        return False
    allowed = min(current_tolerance(a, now, settings), current_tolerance(b, now, settings))
    return abs(a.rating - b.rating) < allowed


def choose_opponent(
    anchor: QueueEntry,
    candidates: Iterable[QueueEntry],
    now: datetime,
    settings: Settings,
    exclude: set[str] | None = None,
) -> QueueEntry | None:
    exclude = exclude or set()
    best: QueueEntry | None = None
    for candidate in candidates:
        if candidate.queue_id == anchor.queue_id or candidate.queue_id in exclude:
            continue
        if not is_compatible(anchor, candidate, now, settings):
            continue
        if best is None:
            best = candidate
            continue
        gap = abs(candidate.rating - anchor.rating)
        best_gap = abs(best.rating - anchor.rating)
        if gap < best_gap or (gap == best_gap and candidate.created_at < best.created_at):
            best = candidate
    return best
