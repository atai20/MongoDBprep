from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.support import auth_header

pytestmark = [pytest.mark.acceptance, pytest.mark.api, pytest.mark.concurrency]


def test_concurrent_http_joins_do_not_exceed_capacity(client, unique_name):
    host = client.post(
        "/api/auth/register",
        json={"username": f"h_{unique_name}", "password": "testpass1"},
    )
    created = client.post(
        "/api/games/",
        json={"name": "Last Slot", "capacity": 2},
        headers=auth_header(host.json()["token"]),
    )
    game_id = created.json()["game_id"]
    tokens = []
    for i in range(4):
        user = client.post(
            "/api/auth/register",
            json={"username": f"j{i}_{unique_name}", "password": "testpass1"},
        )
        tokens.append(user.json()["token"])

    def join(token: str):
        return client.post(f"/api/games/{game_id}/join", headers=auth_header(token))

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(join, tokens))

    stored = client.get(f"/api/games/{game_id}").json()
    assert len(stored["player_ids"]) <= stored["capacity"]
    assert len(stored["player_ids"]) == len(set(stored["player_ids"]))
