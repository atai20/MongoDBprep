from __future__ import annotations

import os
from dataclasses import dataclass, fields, replace
from pathlib import Path

ENV_PREFIX = "MATCHARENA_"


@dataclass(frozen=True)
class Settings:
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "matcharena"
    redis_url: str = "redis://localhost:6379/0"

    min_rating: int = 100
    max_rating: int = 3000
    default_rating: int = 1200

    base_tolerance: int = 50
    tolerance_step: int = 50
    tolerance_interval_seconds: int = 10
    max_tolerance: int = 500

    match_size: int = 2
    game_min_capacity: int = 2
    game_max_capacity: int = 8

    worker_poll_interval_seconds: float = 1.0
    worker_batch_size: int = 200
    candidate_limit: int = 25
    lock_key: str = "matcharena:locks:matchmaker"
    lock_ttl_ms: int = 5000
    worker_heartbeat_ttl_seconds: int = 15

    session_ttl_hours: int = 72
    cors_origins: str = "http://localhost:5173"
    init_indexes_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def _coerce(raw: str, current: object) -> object:
    if isinstance(current, bool):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(current, int):
        return int(raw)
    if isinstance(current, float):
        return float(raw)
    return raw


def _read_dotenv() -> dict[str, str]:
    values: dict[str, str] = {}
    for candidate in (Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"):
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values.setdefault(key.strip(), value.strip())
        break
    return values


def load_settings(**overrides: object) -> Settings:
    settings = Settings()
    env = {**_read_dotenv(), **os.environ}
    updates: dict[str, object] = {}
    for f in fields(Settings):
        raw = env.get(ENV_PREFIX + f.name.upper())
        if raw is not None:
            updates[f.name] = _coerce(raw, getattr(settings, f.name))
    updates.update(overrides)
    return replace(settings, **updates)
