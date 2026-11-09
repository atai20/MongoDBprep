from __future__ import annotations

import threading

import pytest

from tests.support import register_player, run_concurrent

pytestmark = [pytest.mark.acceptance, pytest.mark.concurrency]


def test_ten_simultaneous_enqueue_calls_leave_one_active_entry(container, unique_name):
    player, _ = register_player(container, f"burst-{unique_name}", 1300)
    barrier = threading.Barrier(10)
    container.matchmaking.before_insert = lambda: barrier.wait(timeout=5)

    def enqueue():
        return container.matchmaking.enqueue(player.player_id)

    results = run_concurrent(enqueue, 10)
    failures = [r for r in results if isinstance(r, Exception)]
    assert failures == []
    assert container.queue.count_active_for_player(player.player_id) == 1
    waiting = list(
        container.db["queue_entries"].find({"player_id": player.player_id, "status": "waiting"})
    )
    assert len(waiting) == 1


def test_repeated_enqueue_after_cancel_does_not_stack_active_entries(container, unique_name):
    player, _ = register_player(container, f"stack-{unique_name}", 1260)
    container.matchmaking.enqueue(player.player_id)
    container.matchmaking.cancel(player.player_id)
    barrier = threading.Barrier(6)
    container.matchmaking.before_insert = lambda: barrier.wait(timeout=5)
    run_concurrent(lambda: container.matchmaking.enqueue(player.player_id), 6)
    assert container.queue.count_active_for_player(player.player_id) == 1
