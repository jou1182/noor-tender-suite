"""رادار المنافسات — جسر REST نحو خدمة المزامنة المحلية (Node).

The original Tender Radar code lives untouched in ``radar/`` (vendored from
jou1182/tender-radar-local v1.0.0, scripts layer only). Its sync service
speaks HTTP on http://127.0.0.1:4318; this adapter exposes the read-only
surface to the suite frontend with graceful degradation: when the service
is down every endpoint answers ``{"online": false}`` plus an Arabic hint
instead of raising, so pages render a clear "start the radar" panel.

Endpoints
---------
GET /health   → service liveness + browser/database state
GET /status   → sync state (phase, progress, syncing flag)
GET /tenders  → dashboard snapshot (regions, new/changed items, list)
GET /regions  → per-region counts from the radar dashboard
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

RADAR_BASE = os.getenv("NOOR_RADAR_URL", "http://127.0.0.1:4318").rstrip("/")
TIMEOUT = float(os.getenv("NOOR_RADAR_TIMEOUT", "4"))

OFFLINE_HINT = (
    "خدمة الرادار متوقفة — شغّلها من جذر المنظومة: "
    "npm --prefix radar run start"
)


def _proxy(path: str) -> dict:
    """Forward a GET to the radar sync service; degrade gracefully."""
    url = f"{RADAR_BASE}{path}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            payload = json.loads(r.read().decode("utf-8"))
        if isinstance(payload, dict):
            payload["online"] = True
        return payload
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.info("radar bridge: service unreachable (%s)", exc)
        return {"online": False, "message": OFFLINE_HINT, "service_url": RADAR_BASE}
    except Exception as exc:  # malformed JSON etc. — still report offline shape
        logger.warning("radar bridge: unexpected error (%s)", exc)
        return {"online": False, "message": OFFLINE_HINT, "service_url": RADAR_BASE}


@router.get("/health")
def radar_health() -> dict:
    """Liveness of the vendored sync service plus its browser/database state."""
    return _proxy("/health")


@router.get("/status")
def radar_status() -> dict:
    """Current sync state: phase, message, progress, syncing/downloading flags."""
    return _proxy("/status")


@router.get("/tenders")
def radar_tenders() -> dict:
    """Dashboard snapshot: last sync, region coverage, new/changed tenders."""
    return _proxy("/tenders")


@router.get("/regions")
def radar_regions() -> dict:
    """Per-region tender counts from the radar dashboard API."""
    return _proxy("/dashboard/regions")
