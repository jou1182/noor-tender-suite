"""
Document Normalizer & Model Mapper.

Maps raw Excel BOQ rows and PDF technical-specification extractions into
strongly typed ``BOQLineItem`` and ``ConcreteSpecInput`` Pydantic schemas,
extracting material properties via deterministic pattern matching with
fallback to structured extraction.

The output is shaped to feed ``ValueEngineeringEngine.generate_ve_matrix()``
directly (boq_item / original_spec / qty / unit_rate / exposure_class /
placement_context / candidate).
"""

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from app.parsers.excel_parser import extract_boq_from_buffer, extract_boq_from_workbook
from app.parsers.pdf_parser import extract_structural_specs

# Known VE candidate substitution sources (mirrors ValueEngineeringEngine).
VE_CANDIDATES = {
    "CONC_SRC_C35_OPC": "CONC_SRC_C35_OPC",
    "CONC_SRC_C35_GGBFS": "CONC_SRC_C35_GGBFS",
    "CONC_SRC_LEAN_LOWCEMENT": "CONC_SRC_LEAN_LOWCEMENT",
}

# BOQ description keywords -> VE candidate mapping (deterministic).
DESC_TO_CANDIDATE: List[tuple] = [
    (re.compile(r"slag|ggbfs|pozzolan|fly\s*ash"), "CONC_SRC_C35_GGBFS"),
    (re.compile(r"lean|blinding|low.?cement|fill"), "CONC_SRC_LEAN_LOWCEMENT"),
]


class BOQLineItem(BaseModel):
    """Normalized BOQ line item mapped from raw Excel rows."""

    item_no: str = ""
    description: str
    unit: str = ""
    qty: float = 0.0
    unit_rate: float = 0.0
    total_amount: float = 0.0
    sheet: str = ""

    @field_validator("qty", "unit_rate", "total_amount", mode="before")
    @classmethod
    def _coerce_number(cls, v):
        if v is None or v == "":
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        return float(str(v).replace(",", "").replace("SAR", "").replace("USD", "").strip() or 0)

    @field_validator("description", mode="before")
    @classmethod
    def _strip_description(cls, v):
        return str(v or "").strip()


class ConcreteSpecInput(BaseModel):
    """Structural concrete / steel specification extracted from PDF specs."""

    fc_mpa: Optional[float] = None
    wc: Optional[float] = None
    exposure_class: str = "S1"
    fy_mpa: Optional[float] = None
    cover_depth_mm: Optional[float] = None
    placement_context: str = "EXTERIOR"
    source_sections: List[Dict[str, str]] = Field(default_factory=list)

    @field_validator("exposure_class", mode="before")
    @classmethod
    def _normalize_exposure(cls, v):
        if v is None:
            return "S1"
        val = str(v).upper()
        return val if re.match(r"S[1-4]", val) else "S1"

    @field_validator("placement_context", mode="before")
    @classmethod
    def _normalize_placement(cls, v):
        if v is None:
            return "EXTERIOR"
        val = str(v).upper().replace(" ", "_")
        return val if val in ("CAST_AGAINST_EARTH", "INTERIOR", "EXTERIOR", "CONTINUOUSLY_SUBMERGED") else "EXTERIOR"

    @field_validator("fc_mpa", "wc", "fy_mpa", "cover_depth_mm", mode="before")
    @classmethod
    def _coerce_optional_number(cls, v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


class DocumentNormalizer:
    """Maps raw document extractions into typed VE-ready models."""

    @staticmethod
    def normalize_boq_rows(rows: List[Dict[str, Any]]) -> List[BOQLineItem]:
        """Normalize raw Excel BOQ rows into typed BOQLineItem records."""
        items = []
        for row in rows:
            try:
                items.append(
                    BOQLineItem(
                        item_no=str(row.get("item_no") or ""),
                        description=str(row.get("description") or ""),
                        unit=str(row.get("unit") or ""),
                        qty=row.get("qty") or 0,
                        unit_rate=row.get("unit_rate") or 0,
                        total_amount=row.get("total_amount") or 0,
                        sheet=str(row.get("sheet") or ""),
                    )
                )
            except (ValueError, TypeError):
                continue
        return items

    @staticmethod
    def boq_to_ve_input(item: BOQLineItem, candidate: Optional[str] = None) -> Dict[str, Any]:
        """
        Map a BOQLineItem into the VE engine input contract
        (boq_item / original_spec / qty / unit_rate / exposure_class /
        placement_context / candidate).
        """
        return {
            "boq_item": item.description,
            "original_spec": _infer_original_spec(item.description),
            "qty": item.qty,
            "unit_rate": item.unit_rate,
            "exposure_class": "S1",
            "placement_context": "EXTERIOR",
            "candidate": candidate or _infer_candidate(item.description),
        }

    @staticmethod
    def spec_to_ve_input(spec: ConcreteSpecInput) -> Dict[str, Any]:
        """Map a ConcreteSpecInput into the VE engine input contract."""
        return {
            "boq_item": "Concrete Works",
            "original_spec": _spec_summary(spec),
            "qty": 1.0,
            "unit_rate": 0.0,
            "exposure_class": spec.exposure_class,
            "placement_context": spec.placement_context,
            "candidate": "CONC_SRC_C35_GGBFS",
        }

    @staticmethod
    def build_ve_items(
        workbook_path: Optional[str] = None,
        workbook_buffer: Optional[bytes] = None,
        pdf_path: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Full pipeline: Excel BOQ (+ optional PDF specs) -> VE-ready input items.
        """
        ve_items: List[Dict[str, Any]] = []

        if workbook_path:
            rows = extract_boq_from_workbook(workbook_path)
        elif workbook_buffer is not None:
            rows = extract_boq_from_buffer(workbook_buffer)
        else:
            rows = []

        for item in DocumentNormalizer.normalize_boq_rows(rows):
            ve_items.append(DocumentNormalizer.boq_to_ve_input(item))

        if pdf_path:
            raw_specs = extract_structural_specs(pdf_path)
            spec = ConcreteSpecInput(**raw_specs)
            ve_items.append(DocumentNormalizer.spec_to_ve_input(spec))

        return ve_items


def _infer_original_spec(description: str) -> str:
    """Best-effort original concrete spec inference from description."""
    lowered = description.lower()
    grade = re.search(r"\bC(\d{2})\b", description)
    if grade:
        return f"C{grade.group(1)} OPC"
    if "reinforcement" in lowered or "rebar" in lowered or "steel" in lowered:
        return "Grade 60 Rebar"
    if "cement" in lowered or "concrete" in lowered:
        return "C35 OPC"
    return "C35 OPC"


def _infer_candidate(description: str) -> str:
    """Deterministic candidate mapping from description keywords."""
    lowered = description.lower()
    for pattern, candidate in DESC_TO_CANDIDATE:
        if pattern.search(lowered):
            return candidate
    return "CONC_SRC_C35_GGBFS"


def _spec_summary(spec: ConcreteSpecInput) -> str:
    parts = []
    if spec.fc_mpa is not None:
        parts.append(f"C{int(spec.fc_mpa)}")
    if spec.wc is not None:
        parts.append(f"w/c {spec.wc}")
    if spec.fy_mpa is not None:
        parts.append(f"fy {int(spec.fy_mpa)}")
    if spec.cover_depth_mm is not None:
        parts.append(f"cover {int(spec.cover_depth_mm)}mm")
    return " ".join(parts) if parts else "C35 OPC"
