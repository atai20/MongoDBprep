from __future__ import annotations

import pytest

from matcharena.db.indexes import describe_indexes
from matcharena.db.mongo import GAMES, MATCHES, PLAYERS, QUEUE_ENTRIES, SESSIONS
from tests.support import register_player

pytestmark = [pytest.mark.baseline, pytest.mark.mongo]


def test_indexes_are_installed_on_core_collections(container):
    names = describe_indexes(container.db)
    assert PLAYERS in names
    assert QUEUE_ENTRIES in names
    assert MATCHES in names
    assert GAMES in names
    assert SESSIONS in names
    player_index_names = {idx["name"] for idx in names[PLAYERS]}
    assert "players_username_unique" in player_index_names


def test_player_lookup_and_status_update_persist(container, unique_name):
    player, _ = register_player(container, f"persist-{unique_name}", 1111)
    fetched = container.players.get(player.player_id)
    assert fetched is not None
    assert fetched.rating == 1111
    by_name = container.players.get_by_username(f"persist-{unique_name}")
    assert by_name is not None
    assert by_name.player_id == player.player_id


def test_queue_insert_and_player_lookup_roundtrip(container, unique_name):
    player, _ = register_player(container, f"qpersist-{unique_name}", 1280)
    result = container.matchmaking.enqueue(player.player_id)
    stored = container.queue.get(result.entry.queue_id)
    assert stored is not None
    assert stored.player_id == player.player_id
    assert stored.status.value == "waiting"
    assert container.queue.find_active_for_player(player.player_id).queue_id == stored.queue_id
