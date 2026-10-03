"""ATPAS proposal-builder module — REST wrapper around the embedded ATPAS engine.

The original ATPAS engine code lives untouched in ``atpas_engine/`` (copied from
the private ATPAS repository). This adapter only puts that directory on
``sys.path`` so its absolute imports (``engine.*`` / ``utils.*``) resolve, then
exposes the builder over FastAPI.

Endpoints
---------
GET  /company            → publisher identity (شركة النور للمقاولات)
GET  /projects           → the six project types (water, roads, asphalt…)
GET  /owners             → the twenty owner entities (NWC, Amana, MOH…)
GET  /codes              → active codes for a project
POST /build              → generate a technical-proposal .docx
"""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Embedded-engine bootstrap: make ``engine.*`` and ``utils.*`` importable.
# Repo layout: <repo>/app/api/v1/endpoints/atpas.py → repo root is parents[4].
# ---------------------------------------------------------------------------
ATPAS_ROOT = Path(__file__).resolve().parents[4] / "atpas_engine"
if not ATPAS_ROOT.is_dir():
    raise RuntimeError(f"ATPAS engine module not found at {ATPAS_ROOT}")
if str(ATPAS_ROOT) not in sys.path:
    sys.path.insert(0, str(ATPAS_ROOT))

from engine.builder import Builder  # noqa: E402  (resolved via ATPAS_ROOT)
from utils.json_manager import load_json  # noqa: E402

_CODES_REGISTRY = ATPAS_ROOT / "codes_registry.json"
_MASTER_CONFIG = ATPAS_ROOT / "master_config.json"
_COMPANY_PROFILE = ATPAS_ROOT / "company_profile.json"

_registry_cache: Optional[Dict] = None
_config_cache: Optional[Dict] = None
_builder_cache: Optional[Builder] = None


def _registry() -> Dict:
    global _registry_cache
    if _registry_cache is None:
        _registry_cache = load_json(_CODES_REGISTRY)
    return _registry_cache


def _config() -> Dict:
    global _config_cache
    if _config_cache is None:
        _config_cache = load_json(_MASTER_CONFIG)
    return _config_cache


def _builder() -> Builder:
    global _builder_cache
    if _builder_cache is None:
        _builder_cache = Builder(_registry()["codes"])
    return _builder_cache


@router.get("/company")
def get_company() -> Dict:
    """Publisher identity driving the generated documents."""
    return load_json(_COMPANY_PROFILE)


@router.get("/projects")
def get_projects() -> Dict[str, Dict]:
    """The six engineering project types with their Arabic display names."""
    projects = _config().get("projects", {})
    return {
        pid: {
            "name_ar": p.get("name_ar", pid),
            "name_en": p.get("name_en", pid),
            "networks": p.get("network_types", []),
        }
        for pid, p in projects.items()
    }


@router.get("/owners")
def get_owners() -> Dict[str, Dict]:
    """The twenty owner entities with style bindings and mandatory codes."""
    owners = _config().get("owner_specifications", {})
    return {
        oid: {
            "owner_id": oid,
            "name_ar": o.get("owner_name_ar") or o.get("name_ar", oid),
            "name_en": o.get("owner_name_en") or o.get("name_en", oid),
            "network": o.get("network", ""),
            "mandatory_codes_count": len(o.get("mandatory_codes", [])),
        }
        for oid, o in owners.items()
    }


@router.get("/codes")
def get_codes(project_id: str = Query(..., description="e.g. wastewater, water_supply, asphalt")) -> List[Dict]:
    """Active codes applicable to a project, in sequence order."""
    projects = _config().get("projects", {})
    if project_id not in projects:
        raise HTTPException(status_code=404, detail=f"Unknown project_id: {project_id}")
    codes = [
        c for c in _registry()["codes"].values()
        if c.get("status", "active") == "active" and project_id in c.get("project_ids", [])
    ]
    codes.sort(key=lambda c: c.get("sequence_order", 9999))
    return [
        {
            "code_id": c["code_id"],
            "activity_name_ar": c.get("activity_name_ar", ""),
            "activity_name_en": c.get("activity_name_en", ""),
            "category": c.get("category", ""),
            "sequence_order": c.get("sequence_order", 0),
            "dependencies": c.get("dependencies", []),
        }
        for c in codes
    ]


class BuildRequest(BaseModel):
    project_id: str = Field(..., examples=["wastewater"])
    owner_id: str = Field(..., examples=["nwc"])
    selected_codes: List[str] = Field(..., examples=[["001-SUR-BASE", "002-EXC-FINE"]])


@router.post("/build")
def build_proposal(req: BuildRequest):
    """Assemble the technical proposal .docx from the codes registry."""
    config = _config()
    if req.project_id not in config.get("projects", {}):
        raise HTTPException(status_code=404, detail=f"Unknown project_id: {req.project_id}")
    if req.owner_id not in config.get("owner_specifications", {}):
        raise HTTPException(status_code=404, detail=f"Unknown owner_id: {req.owner_id}")

    known = set(_registry()["codes"].keys())
    unknown = [c for c in req.selected_codes if c not in known]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown codes: {unknown}")

    out_dir = Path(tempfile.gettempdir()) / "noor_atpas_output"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{req.project_id}_{req.owner_id}_proposal.docx"
    output_path = out_dir / safe_name

    ok, message = _builder().build(
        selected_codes=req.selected_codes,
        project_id=req.project_id,
        owner_id=req.owner_id,
        output_path=output_path,
    )
    if not ok:
        raise HTTPException(status_code=500, detail=message or "build failed")

    return FileResponse(
        path=output_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_name,
    )
