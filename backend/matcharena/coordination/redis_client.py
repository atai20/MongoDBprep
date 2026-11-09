from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache

import redis

from matcharena.config import Settings

HEARTBEAT_PREFIX = "matcharena:workers:"


@lru_cache(maxsize=8)
def _client(url: str) -> redis.Redis:
    return redis.Redis.from_url(url, decode_responses=True, socket_timeout=3, socket_connect_timeout=3)


def get_redis(settings: Settings) -> redis.Redis:
    return _client(settings.redis_url)


def ping(client: redis.Redis) -> bool:
    try:
        return bool(client.ping())
    except redis.RedisError:
        return False


def publish_heartbeat(client: redis.Redis, worker_id: str, payload: dict, ttl_seconds: int) -> None:
    client.set(HEARTBEAT_PREFIX + worker_id, json.dumps(payload, default=_json_default), ex=ttl_seconds)


def list_heartbeats(client: redis.Redis) -> list[dict]:
    beats = []
    for key in client.scan_iter(match=HEARTBEAT_PREFIX + "*", count=100):
        raw = client.get(key)
        if raw:
            beats.append(json.loads(raw))
    return sorted(beats, key=lambda b: b.get("worker_id", ""))


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"not serializable: {type(value)!r}")
