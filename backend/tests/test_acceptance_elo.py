from __future__ import annotations

import pytest

from tests.support import enqueue_pair, register_player

pytestmark = [pytest.mark.acceptance, pytest.mark.algorithm]


def test_minimum_rating_players_match_immediately(container, unique_name):
    a, b = enqueue_pair(container, 100, 120, f"minelo-{unique_name}")
    result = container.worker("min-elo").run_cycle()
    assert len(result.matches) == 1
    assert set(result.matches[0].player_ids) == {a.player_id, b.player_id}


def test_maximum_rating_players_match_immediately(container, unique_name):
    a, b = enqueue_pair(container, 3000, 2980, f"maxelo-{unique_name}")
    result = container.worker("max-elo").run_cycle()
    assert len(result.matches) == 1
    assert set(result.matches[0].player_ids) == {a.player_id, b.player_id}


def test_exact_tolerance_boundary_is_inclusive(container, unique_name):
    a, b = enqueue_pair(container, 1000, 1050, f"boundary-{unique_name}")
    result = container.worker("boundary").run_cycle()
    assert len(result.matches) == 1
    assert set(result.matches[0].player_ids) == {a.player_id, b.player_id}


def test_longer_waiting_player_can_match_a_newly_queued_opponent(manual_container, manual_clock, unique_name):
    veteran, _ = register_player(manual_container, f"vet-{unique_name}", 1000)
    manual_container.matchmaking.enqueue(veteran.player_id)
    manual_clock.advance(60)
    newcomer, _ = register_player(manual_container, f"new-{unique_name}", 1080)
    manual_container.matchmaking.enqueue(newcomer.player_id)
    result = manual_container.worker("wait-gap").run_cycle()
    assert len(result.matches) == 1
    assert set(result.matches[0].player_ids) == {veteran.player_id, newcomer.player_id}


def test_high_elo_near_cap_with_expanded_tolerance(manual_container, manual_clock, unique_name):
    a, _ = register_player(manual_container, f"cap-a-{unique_name}", 3000)
    manual_container.matchmaking.enqueue(a.player_id)
    manual_clock.advance(20)
    b, _ = register_player(manual_container, f"cap-b-{unique_name}", 2880)
    manual_container.matchmaking.enqueue(b.player_id)
    result = manual_container.worker("cap-window").run_cycle()
    assert len(result.matches) == 1
