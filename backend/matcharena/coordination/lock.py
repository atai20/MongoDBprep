from __future__ import annotations

import logging
import uuid

import redis

log = logging.getLogger(__name__)


class RedisLock:
    """Lease-style lock shared by matchmaking workers."""

    def __init__(self, client: redis.Redis, key: str, ttl_ms: int, token: str | None = None) -> None:
        self._client = client
        self.key = key
        self.ttl_ms = ttl_ms
        self.token = token or uuid.uuid4().hex
        self._held = False

    @property
    def held(self) -> bool:
        return self._held

    def acquire(self) -> bool:
        acquired = self._client.set(self.key, self.token, nx=True, px=self.ttl_ms)
        self._held = bool(acquired)
        if self._held:
            log.debug("lock acquired", extra={"key": self.key, "token": self.token})
        return self._held

    def owner(self) -> str | None:
        return self._client.get(self.key)

    def remaining_ms(self) -> int:
        return int(self._client.pttl(self.key))

    def release(self) -> bool:
        if not self._held:
            return False
        self._held = False
        released = bool(self._client.delete(self.key))
        log.debug("lock released", extra={"key": self.key, "token": self.token, "released": released})
        return released

    def __enter__(self) -> "RedisLock":
        if not self.acquire():
            raise LockNotAcquired(self.key)
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.release()


class LockNotAcquired(RuntimeError):
    pass


class LockFactory:
    def __init__(self, client: redis.Redis, key: str, ttl_ms: int) -> None:
        self._client = client
        self._key = key
        self._ttl_ms = ttl_ms

    def __call__(self) -> RedisLock:
        return RedisLock(self._client, self._key, self._ttl_ms)
