"""
SSE Event Dispatcher for the swarm telemetry stream.

Provides a lightweight in-process pub/sub hub so backend components (LangGraph
agents, audit orchestration) can publish structured events (e.g.
``rfp_compliance_update``) that the SSE endpoint forwards to connected
dashboard clients in real time.

Design notes:
- Subscriptions capture the event loop they were created on. Publishers may
  run on ANY thread (FastAPI BackgroundTasks, LangGraph nodes); delivery is
  scheduled onto the captured loop via ``asyncio.run_coroutine_threadsafe``.
- ``asyncio.Queue`` instances are bound to the loop they were created on, so a
  queue can only be awaited by that same loop.
"""

import asyncio
import json
import threading
import time
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Set

# event name -> set of subscriber records
class _Subscriber:
    __slots__ = ("queue", "loop")

    def __init__(self, queue: "asyncio.Queue", loop: Optional["asyncio.AbstractEventLoop"]):
        self.queue = queue
        self.loop = loop


_subscribers: DefaultDict[str, Set[_Subscriber]] = defaultdict(set)
_lock = threading.Lock()

_MAX_SUBSCRIBERS_PER_EVENT = 32
_EVENT_TTL_SECONDS = 5.0  # events older than this are dropped for late subscribers


def subscribe(event: str) -> "asyncio.Queue":
    """Create a subscriber queue for the given event name (loop-bound)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    queue: "asyncio.Queue" = asyncio.Queue()
    with _lock:
        _subscribers[event].add(_Subscriber(queue, loop))
        if len(_subscribers[event]) > _MAX_SUBSCRIBERS_PER_EVENT:
            _subscribers[event].clear()
    return queue


def unsubscribe(event: str, queue: "asyncio.Queue") -> None:
    """Remove a subscriber queue for an event."""
    with _lock:
        _subscribers[event] = {
            sub for sub in _subscribers[event] if sub.queue is not queue
        }


def publish(event: str, payload: Any) -> None:
    """
    Publish a structured event to all current subscribers.

    Thread-safe: delivery is scheduled onto each subscriber's captured event
    loop, so this may be called from the event loop thread, a worker thread,
    or a synchronous background task.
    """
    with _lock:
        targets = list(_subscribers.get(event, set()))

    for sub in targets:
        if sub.loop is None or sub.loop.is_closed():
            continue
        asyncio.run_coroutine_threadsafe(_put(sub.queue, event, payload), sub.loop)


async def _put(queue: "asyncio.Queue", event: str, payload: Any) -> None:
    await queue.put({"event": event, "payload": payload, "ts": time.time()})


def encode_sse(event: str, payload: Any) -> str:
    """Serialize an event into an SSE ``data:`` frame."""
    data = json.dumps({"event": event, "payload": payload}, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


async def event_source(
    event: str, initial: Optional[List[Dict[str, Any]]] = None
):
    """
    Async generator yielding SSE frames for an event, draining any initial
    payloads first (e.g. compliance results already computed before the
    dashboard connected).
    """
    for item in initial or []:
        yield encode_sse(event, item)

    queue = subscribe(event)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                if time.time() - msg["ts"] > _EVENT_TTL_SECONDS:
                    continue
                yield encode_sse(msg["event"], msg["payload"])
            except asyncio.TimeoutError:
                # Keep the stream alive (SSE heartbeat comment).
                yield ": keep-alive\n\n"
    finally:
        unsubscribe(event, queue)
