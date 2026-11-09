from __future__ import annotations

import logging

from matcharena.config import load_settings
from matcharena.coordination.redis_client import get_redis, ping as redis_ping
from matcharena.db.indexes import ensure_indexes
from matcharena.db.mongo import get_database, ping as mongo_ping
from matcharena.logging_setup import configure_logging

log = logging.getLogger("matcharena.scripts.init_db")


def main() -> None:
    configure_logging()
    settings = load_settings()
    db = get_database(settings)
    if not mongo_ping(db):
        raise SystemExit(f"MongoDB is not reachable at {settings.mongo_uri}")
    redis_client = get_redis(settings)
    if not redis_ping(redis_client):
        raise SystemExit(f"Redis is not reachable at {settings.redis_url}")
    created = ensure_indexes(db)
    log.info("database ready", extra={"db": settings.mongo_db, "indexes": created})
    print(f"initialized {settings.mongo_db}: {created}")


if __name__ == "__main__":
    main()
