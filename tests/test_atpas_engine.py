# -*- coding: utf-8 -*-
"""Tests for the embedded ATPAS proposal-builder module (atpas_engine)."""

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
ATPAS_ROOT = REPO_ROOT / "atpas_engine"
if str(ATPAS_ROOT) not in sys.path:
    sys.path.insert(0, str(ATPAS_ROOT))

from engine.builder import Builder  # noqa: E402
from utils.json_manager import load_json  # noqa: E402

REGISTRY = load_json(ATPAS_ROOT / "codes_registry.json")
CONFIG = load_json(ATPAS_ROOT / "master_config.json")
PROFILE = load_json(ATPAS_ROOT / "company_profile.json")


# ---------------------------------------------------------------------------
# Data integrity & rebrand guards
# ---------------------------------------------------------------------------

class TestRegistryIntegrity:
    def test_registry_has_expected_scale(self):
        # 65 base codes + 5 excavation support codes
        assert len(REGISTRY["codes"]) == 70

    def test_active_codes_present(self):
        active = [c for c in REGISTRY["codes"].values() if c.get("status") == "active"]
        assert len(active) == 70

    def test_no_alrawaf_anywhere_in_engine_data(self):
        raw = (ATPAS_ROOT / "codes_registry.json").read_text(encoding="utf-8")
        raw += (ATPAS_ROOT / "master_config.json").read_text(encoding="utf-8")
        raw += (ATPAS_ROOT / "company_profile.json").read_text(encoding="utf-8")
        for banned in ("الرواف", "Al-Rawaf", "alrawaf", "ALRAWAF"):
            assert banned not in raw

    def test_company_profile_is_alnoor(self):
        assert PROFILE["company_name_ar"] == "النور"
        assert PROFILE["company_name_en"] == "Al-Noor"


# ---------------------------------------------------------------------------
# Engine-level build (headless, no source_documents — gap-tolerant)
# ---------------------------------------------------------------------------

class TestEngineBuild:
    def _codes_for(self, project_id, n=3):
        codes = [
            c for c in REGISTRY["codes"].values()
            if c.get("status") == "active" and project_id in c.get("project_ids", [])
        ]
        codes.sort(key=lambda c: c.get("sequence_order", 9999))
        return [c["code_id"] for c in codes[:n]]

    def test_build_wastewater_docx(self, tmp_path):
        owner = "nwc"  # National Water Company style exists in style_templates
        selected = self._codes_for("wastewater", 3)
        builder = Builder(REGISTRY["codes"])
        out = tmp_path / "proposal.docx"
        ok, message = builder.build(
            selected_codes=selected,
            project_id="wastewater",
            owner_id=owner,
            output_path=out,
        )
        assert ok, message
        assert out.exists() and out.stat().st_size > 0

    def test_build_output_contains_arabic_activity(self, tmp_path):
        selected = self._codes_for("water_supply", 2)
        builder = Builder(REGISTRY["codes"])
        out = tmp_path / "proposal.docx"
        ok, _ = builder.build(selected, "water_supply", "nwc", out)
        assert ok
        from docx import Document
        doc = Document(out)
        text = "\n".join(p.text for p in doc.paragraphs)
        assert len(text.strip()) > 0


# ---------------------------------------------------------------------------
# REST wrapper
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from app.main import app
    return TestClient(app)


class TestAtpasAPI:
    def test_company_endpoint(self, client):
        r = client.get("/api/v1/atpas/company")
        assert r.status_code == 200
        assert r.json()["company_name_ar"] == "النور"

    def test_projects_endpoint(self, client):
        r = client.get("/api/v1/atpas/projects")
        assert r.status_code == 200
        projects = r.json()
        assert "wastewater" in projects
        assert len(projects) == 6

    def test_owners_endpoint(self, client):
        r = client.get("/api/v1/atpas/owners")
        assert r.status_code == 200
        assert len(r.json()) == 20

    def test_codes_endpoint(self, client):
        r = client.get("/api/v1/atpas/codes", params={"project_id": "asphalt"})
        assert r.status_code == 200
        codes = r.json()
        assert len(codes) > 0
        assert all(c["code_id"] for c in codes)

    def test_codes_endpoint_unknown_project(self, client):
        r = client.get("/api/v1/atpas/codes", params={"project_id": "nope"})
        assert r.status_code == 404

    def test_build_endpoint(self, client):
        r = client.get("/api/v1/atpas/codes", params={"project_id": "road_maintenance"})
        selected = [c["code_id"] for c in r.json()[:3]]
        r = client.post("/api/v1/atpas/build", json={
            "project_id": "road_maintenance",
            "owner_id": "mot",
            "selected_codes": selected,
        })
        assert r.status_code == 200
        assert r.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument"
        )
        assert len(r.content) > 0

    def test_build_endpoint_rejects_unknown_code(self, client):
        r = client.post("/api/v1/atpas/build", json={
            "project_id": "wastewater",
            "owner_id": "nwc",
            "selected_codes": ["000-FAKE-CODE"],
        })
        assert r.status_code == 422
