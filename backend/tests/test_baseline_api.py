from __future__ import annotations

import pytest

from tests.support import auth_header, register_player

pytestmark = [pytest.mark.baseline, pytest.mark.api]


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_reports_mongo_and_redis(client):
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["mongo"] is True
    assert body["redis"] is True


def test_register_login_and_profile_roundtrip(client, unique_name):
    registered = client.post(
        "/api/auth/register",
        json={"username": f"user_{unique_name}", "password": "testpass1", "rating": 1400},
    )
    assert registered.status_code == 201
    token = registered.json()["token"]
    me = client.get("/api/me", headers=auth_header(token))
    assert me.status_code == 200
    player = me.json()["player"]
    assert player["rating"] == 1400
    assert player["status"] == "idle"

    login = client.post(
        "/api/auth/login",
        json={"username": f"user_{unique_name}", "password": "testpass1"},
    )
    assert login.status_code == 200
    assert login.json()["player_id"] == player["player_id"]


def test_duplicate_username_is_rejected(client, unique_name):
    payload = {"username": f"dup_{unique_name}", "password": "testpass1"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    again = client.post("/api/auth/register", json=payload)
    assert again.status_code == 409
    assert again.json()["error"] == "username_taken"


def test_protected_routes_require_auth(client):
    assert client.get("/api/me").status_code == 401
    assert client.post("/api/matchmaking/queue").status_code == 401
    assert client.post("/api/games/", json={"name": "Test Lobby", "capacity": 2}).status_code == 401


def test_sequential_enqueue_is_idempotent(client, unique_name):
    registered = client.post(
        "/api/auth/register",
        json={"username": f"q_{unique_name}", "password": "testpass1", "rating": 1300},
    )
    headers = auth_header(registered.json()["token"])
    first = client.post("/api/matchmaking/queue", headers=headers)
    second = client.post("/api/matchmaking/queue", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created"] is True
    assert second.json()["created"] is False
    assert first.json()["entry"]["queue_id"] == second.json()["entry"]["queue_id"]
    status = client.get("/api/matchmaking/status", headers=headers)
    assert status.json()["state"] == "waiting"


def test_cancel_then_rejoin_creates_waiting_entry(container, unique_name):
    player, _ = register_player(container, f"rejoin-{unique_name}", 1250)
    first = container.matchmaking.enqueue(player.player_id)
    cancelled = container.matchmaking.cancel(player.player_id)
    assert cancelled.status.value == "cancelled"
    again = container.matchmaking.enqueue(player.player_id)
    assert again.entry.status.value == "waiting"
    assert container.queue.count_active_for_player(player.player_id) == 1


def test_create_join_and_leave_lobby_sequentially(client, unique_name):
    host = client.post(
        "/api/auth/register",
        json={"username": f"host_{unique_name}", "password": "testpass1"},
    )
    guest = client.post(
        "/api/auth/register",
        json={"username": f"guest_{unique_name}", "password": "testpass1"},
    )
    host_headers = auth_header(host.json()["token"])
    guest_headers = auth_header(guest.json()["token"])
    created = client.post(
        "/api/games/",
        json={"name": "Practice Room", "capacity": 3},
        headers=host_headers,
    )
    assert created.status_code == 201
    game_id = created.json()["game_id"]
    assert host.json()["player_id"] in created.json()["player_ids"]

    joined = client.post(f"/api/games/{game_id}/join", headers=guest_headers)
    assert joined.status_code == 200
    assert guest.json()["player_id"] in joined.json()["player_ids"]

    left = client.post(f"/api/games/{game_id}/leave", headers=guest_headers)
    assert left.status_code == 200
    assert guest.json()["player_id"] not in left.json()["player_ids"]
