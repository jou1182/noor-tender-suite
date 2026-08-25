"""
Addenda Diff & Delta Engine.

Parses new tender addenda (PDF / DOCX / Excel bulletins), diffs the content
against the current ``OverallTenderState`` baseline, and classifies each delta
by impact severity:

  - HIGH   — Structural / cost variance > 5%
  - MEDIUM — Schedule / deadline changes
  - LOW    — Typographical / clarity corrections
"""

import re
from typing import Any, Dict, List

from app.parsers.pdf_parser import extract_rich_text
from app.schemas.clarifications import (
    AddendumDeltaItem,
    AddendumImpactSummary,
    TenderAddendum,
)

DEADLINE_KEYWORDS = ("deadline", "due date", "submission date", "extension", "milestone")
COST_KEYWORDS = ("rate", "unit rate", "amount", "sar", "price", "boq", "quantity")
STRUCTURAL_KEYWORDS = ("sbc", "structural", "concrete", "rebar", "cover", "fy", "f'c")


class AddendaDiffEngine:
    """Deterministic addendum parser + diff analyzer."""

    @staticmethod
    def extract_text(path: str, doc_type: str = "pdf") -> str:
        """Extract raw text from an addendum file based on its type."""
        if doc_type == "pdf":
            return extract_rich_text(path)
        if doc_type == "docx":
            from docx import Document

            doc = Document(path)
            return "\n".join(p.text for p in doc.paragraphs)
        if doc_type == "xlsx":
            from app.parsers.excel_parser import extract_boq_from_workbook

            rows = extract_boq_from_workbook(path)
            return "\n".join(
                f"{r['item_no']}\t{r['description']}\t{r['qty']}\t{r['unit_rate']}\t{r['total_amount']}"
                for r in rows
            )
        return ""

    @staticmethod
    def parse_addendum(path: str, doc_type: str = "pdf", addendum_id: str = "", title: str = "") -> TenderAddendum:
        """Parse an addendum file into a TenderAddendum with raw text + parsed items."""
        text = AddendaDiffEngine.extract_text(path, doc_type)
        parsed: List[Dict[str, Any]] = []

        # Extract tabular BOQ-like lines (item_no description qty rate total).
        for line in text.splitlines():
            parts = [p for p in re.split(r"\s{2,}|\t", line.strip()) if p]
            if len(parts) >= 4 and parts[0].replace(".", "").isdigit():
                try:
                    parsed.append(
                        {
                            "item_no": parts[0],
                            "description": parts[1],
                            "qty": float(parts[-3].replace(",", "")),
                            "unit_rate": float(parts[-2].replace(",", "")),
                            "total_amount": float(parts[-1].replace(",", "")),
                        }
                    )
                except (ValueError, IndexError):
                    continue

        return TenderAddendum(
            addendum_id=addendum_id,
            title=title,
            source_path=path,
            document_type=doc_type,
            raw_text=text,
            parsed_items=parsed,
        )

    @staticmethod
    def _classify_severity(line: str) -> str:
        lowered = line.lower()
        if any(kw in lowered for kw in STRUCTURAL_KEYWORDS) and any(kw in lowered for kw in COST_KEYWORDS):
            return "HIGH"
        if any(kw in lowered for kw in DEADLINE_KEYWORDS):
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def diff_clauses(base_text: str, addendum_text: str) -> List[AddendumDeltaItem]:
        """Structural text diff across clause lines."""
        import difflib

        deltas: List[AddendumDeltaItem] = []
        base_lines = set(base_text.splitlines())
        add_lines = set(addendum_text.splitlines())

        for line in add_lines - base_lines:
            if not line.strip():
                continue
            severity = AddendaDiffEngine._classify_severity(line)
            reference = ""
            m = re.search(r"(?:Clause|Section|Item)\s*([\d.]+)", line, re.IGNORECASE)
            if m:
                reference = m.group(1)
            deltas.append(
                AddendumDeltaItem(
                    delta_type="clause",
                    reference=reference or "UNKNOWN",
                    base_value="",
                    new_value=line,
                    severity=severity,
                    description=f"Added/changed clause text: {line[:120]}",
                )
            )
        return deltas

    @staticmethod
    def diff_boq(base_items: List[Dict[str, Any]], addendum_items: List[Dict[str, Any]]) -> List[AddendumDeltaItem]:
        """Diff BOQ line items (qty/rate/total) and flag cost variance severity."""
        deltas: List[AddendumDeltaItem] = []
        base_map = {i.get("item_no", i.get("description")): i for i in base_items}
        add_map = {i.get("item_no", i.get("description")): i for i in addendum_items}

        for key in set(base_map) | set(add_map):
            base = base_map.get(key, {})
            add = add_map.get(key, {})
            base_total = float(base.get("total_amount", 0) or 0)
            add_total = float(add.get("total_amount", 0) or 0)

            if abs(add_total - base_total) <= 0.01 and base.get("description") == add.get("description"):
                continue

            severity = "HIGH"
            if base_total and add_total:
                variance = abs(add_total - base_total) / base_total
                severity = "HIGH" if variance > 0.05 else ("MEDIUM" if variance > 0.0 else "LOW")
            deltas.append(
                AddendumDeltaItem(
                    delta_type="boq",
                    reference=str(key),
                    base_value=str(base_total),
                    new_value=str(add_total),
                    severity=severity,
                    description=(
                        f"BOQ item {key}: total {base_total:,.2f} -> {add_total:,.2f} "
                        f"(delta {add_total - base_total:+,.2f} SAR)"
                    ),
                )
            )
        return deltas

    @staticmethod
    def diff_deadlines(base_text: str, addendum_text: str) -> List[AddendumDeltaItem]:
        """Detect deadline / date extensions."""
        deltas: List[AddendumDeltaItem] = []
        date_pattern = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
        for line in addendum_text.splitlines():
            if any(kw in line.lower() for kw in DEADLINE_KEYWORDS) and date_pattern.search(line):
                deltas.append(
                    AddendumDeltaItem(
                        delta_type="deadline",
                        reference="DEADLINE",
                        base_value="",
                        new_value=line,
                        severity="MEDIUM",
                        description=f"Deadline change detected: {line.strip()[:120]}",
                    )
                )
        return deltas

    @staticmethod
    def analyze(
        base_state: Dict[str, Any],
        addendum: TenderAddendum,
        addendum_id: str = "",
    ) -> AddendumImpactSummary:
        """Full delta analysis: clauses + BOQ + deadlines against baseline state."""
        base_text = str(base_state.get("raw_specs_text", base_state.get("rfp_text", "")) or "")
        base_boq = base_state.get("boq_items", []) or []

        deltas: List[AddendumDeltaItem] = []
        deltas.extend(AddendaDiffEngine.diff_clauses(base_text, addendum.raw_text))
        deltas.extend(AddendaDiffEngine.diff_boq(base_boq, addendum.parsed_items))
        deltas.extend(AddendaDiffEngine.diff_deadlines(base_text, addendum.raw_text))

        total_cost_variance = sum(
            (float(d.new_value or 0) - float(d.base_value or 0)) for d in deltas if d.delta_type == "boq"
        )
        reaudited = [
            d.reference for d in deltas if d.delta_type == "boq" and d.severity == "HIGH"
        ]

        return AddendumImpactSummary(
            addendum_id=addendum_id or addendum.addendum_id,
            total_deltas=len(deltas),
            high_impact_count=sum(1 for d in deltas if d.severity == "HIGH"),
            medium_impact_count=sum(1 for d in deltas if d.severity == "MEDIUM"),
            low_impact_count=sum(1 for d in deltas if d.severity == "LOW"),
            total_cost_variance_sar=round(total_cost_variance, 2),
            reaudited_items=reaudited,
            deadline_extension_days=0,
            deltas=deltas,
        )
