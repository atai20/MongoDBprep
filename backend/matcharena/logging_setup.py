from __future__ import annotations

import logging
import os

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {k: v for k, v in record.__dict__.items() if k not in _RESERVED}
        if not extras:
            return base
        return base + " " + " ".join(f"{k}={v}" for k, v in sorted(extras.items()))


def configure_logging(level: str | None = None) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level or os.environ.get("MATCHARENA_LOG_LEVEL", "INFO"))
    logging.getLogger("pymongo").setLevel(logging.WARNING)
