from __future__ import annotations

import time

import pytest

from matcharena.coordination.lock import RedisLock

pytestmark = [pytest.mark.acceptance, pytest.mark.redis]


def test_expired_lock_cannot_be_released_by_the_original_owner(container):
    key = "matcharena:test:lock"
    first = RedisLock(container.redis, key, ttl_ms=40, token="owner-a")
    second = RedisLock(container.redis, key, ttl_ms=500, token="owner-b")
    assert first.acquire()
    time.sleep(0.08)
    assert second.acquire()
    assert second.owner() == "owner-b"
    first.release()
    assert second.owner() == "owner-b"
    assert second.remaining_ms() > 0
    second.release()


def test_lock_release_is_tied_to_ownership_token(container):
    key = "matcharena:test:lock-token"
    holder = RedisLock(container.redis, key, ttl_ms=1000, token="keeper")
    interloper = RedisLock(container.redis, key, ttl_ms=1000, token="intruder")
    assert holder.acquire()
    interloper._held = True
    interloper.release()
    assert holder.owner() == "keeper"
    holder.release()
