"""
Swarm Telemetry Bus.

Thread-safe in-process ring buffer that lets LangGraph agents publish real-time
execution telemetry (status transitions, compliance findings) which the SSE
endpoint (`/api/v1/telemetry/stream`) drains and streams to connected dashboards.

The buffer is best-effort: if no agent has published since the last drain, the
SSE generator falls back to its scripted demonstration sequence.
"""

import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import List, Optional

_MAX_EVENTS = 64

_buffer: "deque[str]" = deque(maxlen=_MAX_EVENTS)
_lock = threading.Lock()


def emit(message: str, source: Optional[str] = "AGENT") -> None:
    """Publish a telemetry line to the shared bus (safe across agent threads)."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [AGENT_TELEMETRY] {message}"
    with _lock:
        _buffer.append(line)


def drain(max_items: int = _MAX_EVENTS) -> List[str]:
    """Atomically pull and clear all buffered telemetry lines."""
    with _lock:
        items = list(_buffer)
        _buffer.clear()
    return items[-max_items:]


def clear() -> None:
    """Clear the buffer (used by tests)."""
    with _lock:
        _buffer.clear()


def count() -> int:
    with _lock:
        return len(_buffer)


def _now_ms() -> int:
    return int(time.time() * 1000)