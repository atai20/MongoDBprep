from __future__ import annotations

import threading

import pytest

from tests.support import enqueue_pair

pytestmark = [pytest.mark.acceptance, pytest.mark.concurrency]


def test_two_workers_do_not_create_duplicate_matches(container, unique_name):
    a, b = enqueue_pair(container, 1500, 1520, f"dupmatch-{unique_name}")
    barrier = threading.Barrier(2)
    w1 = container.worker("w1")
    w2 = container.worker("w2")
    w1.after_scan = lambda _waiting: barrier.wait(timeout=5)
    w2.after_scan = lambda _waiting: barrier.wait(timeout=5)

    outcomes: list[object] = []

    def run(worker):
        outcomes.append(worker.run_cycle())

    t1 = threading.Thread(target=run, args=(w1,))
    t2 = threading.Thread(target=run, args=(w2,))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    current_a = container.matches.count_current_for_player(a.player_id)
    current_b = container.matches.count_current_for_player(b.player_id)
    assert current_a == 1
    assert current_b == 1
    docs = list(
        container.db["matches"].find(
            {"player_ids": a.player_id, "status": {"$in": ["pending", "active"]}}
        )
    )
    assert len(docs) == 1


def test_cancelled_player_is_not_matched(container, unique_name):
    a, _b = enqueue_pair(container, 1600, 1610, f"cancelrace-{unique_name}")
    worker = container.worker("cancel-worker")

    def cancel_during_reserve(left, _right):
        if left.player_id == a.player_id:
            container.matchmaking.cancel(a.player_id)

    worker.before_reserve = cancel_during_reserve
    worker.run_cycle()

    latest = container.queue.find_latest_for_player(a.player_id)
    assert latest is not None
    assert latest.status.value == "cancelled"
    assert container.matches.count_current_for_player(a.player_id) == 0
    player = container.players.get(a.player_id)
    assert player.status.value != "matched"
