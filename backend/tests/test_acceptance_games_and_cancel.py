from __future__ import annotations

import threading

import pytest

from matcharena.domain.models import Game, GameStatus
from tests.support import register_player, run_concurrent

pytestmark = [pytest.mark.acceptance, pytest.mark.concurrency]


def _open_lobby(container, host_id: str, capacity: int, occupants: list[str]) -> Game:
    now = container.clock.now()
    game = Game(
        game_id=f"game-{host_id[:8]}",
        match_id=None,
        capacity=capacity,
        status=GameStatus.OPEN,
        created_at=now,
        player_ids=list(occupants),
        host_id=host_id,
        name="Load Test Lobby",
    )
    return container.games.insert(game)


def test_same_player_cannot_join_a_game_twice_under_concurrency(container, unique_name):
    host, _ = register_player(container, f"host-{unique_name}", 1200)
    player, _ = register_player(container, f"joiner-{unique_name}", 1210)
    game = _open_lobby(container, host.player_id, capacity=4, occupants=[host.player_id])
    barrier = threading.Barrier(8)
    container.game_service.before_join_write = lambda _game: barrier.wait(timeout=5)

    def join():
        return container.game_service.join(game.game_id, player.player_id)

    run_concurrent(join, 8)
    stored = container.games.get(game.game_id)
    assert stored is not None
    assert stored.player_ids.count(player.player_id) == 1


def test_two_players_cannot_take_the_last_slot(container, unique_name):
    host, _ = register_player(container, f"cap-host-{unique_name}", 1200)
    p1, _ = register_player(container, f"slot-a-{unique_name}", 1210)
    p2, _ = register_player(container, f"slot-b-{unique_name}", 1220)
    game = _open_lobby(container, host.player_id, capacity=2, occupants=[host.player_id])
    barrier = threading.Barrier(2)
    container.game_service.before_join_write = lambda _game: barrier.wait(timeout=5)

    outcomes = []

    def join(player_id: str):
        try:
            outcomes.append(container.game_service.join(game.game_id, player_id))
        except Exception as exc:  # noqa: BLE001
            outcomes.append(exc)

    t1 = threading.Thread(target=join, args=(p1.player_id,))
    t2 = threading.Thread(target=join, args=(p2.player_id,))
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    stored = container.games.get(game.game_id)
    assert stored is not None
    assert len(stored.player_ids) <= stored.capacity
    assert len(set(stored.player_ids)) == len(stored.player_ids)
