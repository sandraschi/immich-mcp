"""In-memory ring buffer for recent log lines (webapp /logs endpoint)."""

import logging
import threading
from collections import deque
from datetime import datetime


class _RingBufferHandler(logging.Handler):
    def __init__(self, capacity: int = 500) -> None:
        super().__init__(level=logging.INFO)
        self._capacity = capacity
        self._records: deque[str] = deque(maxlen=capacity)
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = (
                f"{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')} "
                f"{record.levelname:7s} {record.name}: {record.getMessage()}"
            )
            with self._lock:
                self._records.append(line)
        except Exception:
            pass

    def snapshot(self, limit: int) -> list[str]:
        with self._lock:
            items = list(self._records)
        return items[-limit:]


_handler = _RingBufferHandler()


def install_log_capture() -> None:
    """Attach the ring buffer to the immich_mcp logger tree (idempotent)."""
    if not any(isinstance(h, _RingBufferHandler) for h in logging.getLogger("immich_mcp").handlers):
        logging.getLogger("immich_mcp").addHandler(_handler)
    # Also capture uvicorn access/error lines so API activity shows up.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        if not any(isinstance(h, _RingBufferHandler) for h in logger.handlers):
            logger.addHandler(_handler)


def get_recent_logs(limit: int = 200) -> list[str]:
    """Return the most recent captured log lines."""
    return _handler.snapshot(limit)
