from __future__ import annotations

import pytest

from matcharena.config import Settings
from matcharena.domain import elo
from matcharena.domain.clock import ManualClock
from matcharena.domain.models import QueueEntry, QueueStatus
from tests.support import enqueue_pair, register_player

pytestmark = [pytest.mark.baseline, pytest.mark.algorithm]


def _settings() -> Settings:
    return Settings()


def test_tolerance_expands_every_ten_seconds_and_caps():
    settings = _settings()
    assert elo.tolerance_for_wait(0, settings) == 50
    assert elo.tolerance_for_wait(9.9, settings) == 50
    assert elo.tolerance_for_wait(10, settings) == 100
    assert elo.tolerance_for_wait(60, settings) == 350
    assert elo.tolerance_for_wait(10_000, settings) == 500


def test_mid_range_players_within_base_tolerance_match(container, unique_name):
    a, b = enqueue_pair(container, 1200, 1230, f"mid-{unique_name}")
    worker = container.worker("baseline-mid")
    result = worker.run_cycle()
    assert len(result.matches) == 1
    match = result.matches[0]
    assert set(match.player_ids) == {a.player_id, b.player_id}
    assert container.matches.count_current_for_player(a.player_id) == 1
    assert container.queue.count_active_for_player(a.player_id) == 0
    assert container.queue.find_latest_for_player(a.player_id).status.value == "matched"


def test_empty_queue_creates_no_match(container):
    result = container.worker("baseline-empty").run_cycle()
    assert result.scanned == 0
    assert result.matches == []


def test_single_waiting_player_is_not_matched(container, unique_name):
    player, _ = register_player(container, f"solo-{unique_name}", 1400)
    container.matchmaking.enqueue(player.player_id)
    result = container.worker("baseline-solo").run_cycle()
    assert result.matches == []
    assert container.queue.count_active_for_player(player.player_id) == 1


def test_incompatible_mid_range_players_do_not_match_immediately(container, unique_name):
    enqueue_pair(container, 1200, 1400, f"far-{unique_name}")
    result = container.worker("baseline-far").run_cycle()
    assert result.matches == []


def test_choose_opponent_picks_closest_rating():
    settings = _settings()
    clock = ManualClock()
    now = clock.now()
    anchor = QueueEntry("a", "p1", 1200, QueueStatus.WAITING, now, now)
    close = QueueEntry("b", "p2", 1220, QueueStatus.WAITING, now, now)
    farther = QueueEntry("c", "p3", 1240, QueueStatus.WAITING, now, now)
    chosen = elo.choose_opponent(anchor, [farther, close], now, settings)
    assert chosen is not None
    assert chosen.queue_id == "b"
