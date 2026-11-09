from __future__ import annotations

import argparse
import logging
import signal
import threading

from matcharena.config import load_settings
from matcharena.container import build_container
from matcharena.coordination.redis_client import publish_heartbeat
from matcharena.logging_setup import configure_logging
from matcharena.workers.matchmaker import CycleResult

log = logging.getLogger("matcharena.workers")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MatchArena matchmaking workers")
    parser.add_argument("--threads", type=int, default=1, help="worker loops to run in this process")
    parser.add_argument("--once", action="store_true", help="run a single cycle per worker and exit")
    args = parser.parse_args()

    configure_logging()
    settings = load_settings()
    container = build_container(settings)
    stop = threading.Event()

    def handle_signal(signum, _frame):
        log.info("shutdown requested", extra={"signal": signum})
        stop.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    workers = []
    for _ in range(max(1, args.threads)):
        worker = container.worker()

        def heartbeat(result: CycleResult, worker_id: str = worker.worker_id) -> None:
            publish_heartbeat(
                container.redis,
                worker_id,
                {
                    "worker_id": worker_id,
                    "at": container.clock.now(),
                    "skipped": result.skipped,
                    "scanned": result.scanned,
                    "matches": len(result.matches),
                    "errors": result.errors,
                },
                settings.worker_heartbeat_ttl_seconds,
            )

        worker.on_cycle = heartbeat
        workers.append(worker)

    if args.once:
        for worker in workers:
            result = worker.run_once()
            log.info(
                "single cycle finished",
                extra={"worker_id": worker.worker_id, "scanned": result.scanned, "matches": len(result.matches)},
            )
        return

    threads = [
        threading.Thread(target=w.run_forever, args=(stop,), name=w.worker_id, daemon=True) for w in workers
    ]
    for t in threads:
        t.start()
    while any(t.is_alive() for t in threads):
        for t in threads:
            t.join(timeout=0.5)


if __name__ == "__main__":
    main()
