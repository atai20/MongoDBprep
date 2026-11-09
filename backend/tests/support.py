from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar

from matcharena.container import Container

T = TypeVar("T")


def register_player(container: Container, username: str, rating: int, password: str = "testpass1"):
    player, token = container.auth.register(username, password, rating)
    return player, token


def enqueue_pair(container: Container, rating_a: int, rating_b: int, prefix: str):
    a, _ = register_player(container, f"{prefix}-a", rating_a)
    b, _ = register_player(container, f"{prefix}-b", rating_b)
    container.matchmaking.enqueue(a.player_id)
    container.matchmaking.enqueue(b.player_id)
    return a, b


def run_concurrent(fn: Callable[[], T], n: int) -> list[T | Exception]:
    barrier = threading.Barrier(n)
    results: list[T | Exception] = []
    lock = threading.Lock()

    def wrapped() -> None:
        barrier.wait(timeout=5)
        try:
            value = fn()
            outcome: T | Exception = value
        except Exception as exc:  # noqa: BLE001 - tests collect worker failures
            outcome = exc
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=wrapped) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    return results


def run_pool(fns: list[Callable[[], T]]) -> list[T | Exception]:
    results: list[T | Exception] = []
    with ThreadPoolExecutor(max_workers=len(fns)) as pool:
        futures = [pool.submit(fn) for fn in fns]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:  # noqa: BLE001
                results.append(exc)
    return results


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
