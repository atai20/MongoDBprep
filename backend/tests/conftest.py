from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from matcharena.api.app import create_app
from matcharena.config import load_settings
from matcharena.container import build_container
from matcharena.coordination.redis_client import ping as redis_ping
from matcharena.db.indexes import ensure_indexes
from matcharena.db.mongo import ping as mongo_ping
from matcharena.domain.clock import ManualClock, SystemClock


@pytest.fixture(scope="session")
def settings():
    return load_settings(
        mongo_db="matcharena_test",
        redis_url="redis://localhost:6379/15",
        init_indexes_on_startup=True,
        lock_ttl_ms=5000,
        worker_batch_size=200,
        candidate_limit=25,
    )


@pytest.fixture(scope="session")
def _session_container(settings):
    container = build_container(settings, clock=SystemClock())
    if not mongo_ping(container.db):
        pytest.fail(
            f"MongoDB is not reachable at {settings.mongo_uri}. "
            "Start it with: docker compose up -d mongo redis"
        )
    if not redis_ping(container.redis):
        pytest.fail(
            f"Redis is not reachable at {settings.redis_url}. "
            "Start it with: docker compose up -d mongo redis"
        )
    ensure_indexes(container.db)
    return container


@pytest.fixture
def container(_session_container, settings):
    db = _session_container.db
    for name in db.list_collection_names():
        if name.startswith("system."):
            continue
        db[name].delete_many({})
    _session_container.redis.flushdb()
    fresh = build_container(
        settings,
        db=db,
        redis_client=_session_container.redis,
        clock=SystemClock(),
    )
    ensure_indexes(fresh.db)
    return fresh


@pytest.fixture
def app(container, settings):
    return create_app(settings, container)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def unique_name():
    return uuid.uuid4().hex[:10]


@pytest.fixture
def manual_clock():
    return ManualClock()


@pytest.fixture
def manual_container(container, settings, manual_clock):
    return build_container(
        settings,
        db=container.db,
        redis_client=container.redis,
        clock=manual_clock,
    )
