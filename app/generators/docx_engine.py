"""
DOCX Document Assembler.

Builds a professionally formatted technical proposal .docx using python-docx:

  - Custom cover page (project title, client, contractor branding, date)
  - Running header (contractor logo text / project code) and footer
    (Page X of Y + confidentiality notice)
  - Styled tables with header shading (BOQ, Compliance Matrix, VE Savings)
  - Callout boxes (Warning / Note) for contractual risk highlights
"""

from datetime import datetime
from typing import Any, Dict, List

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

PRIMARY = RGBColor(0x0F, 0x76, 0x6E)      # teal
DARK = RGBColor(0x0F, 0x17, 0x2A)         # slate-950
WARNING_BG = "FEF3C7"                     # amber-100
NOTE_BG = "DBEAFE"                        # blue-100
HEADER_BG = "0F172A"                      # dark table header


def _shade(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


class DocxProposalGenerator:
    """Enterprise-formatted DOCX proposal assembler."""

    def __init__(self, contractor_name: str = "ConTech AI Contracting Co.") -> None:
        self.contractor = contractor_name

    def generate(self, context: Dict[str, Any], output_path: str) -> str:
        doc = Document()

        self._setup_page(doc)
        self._add_cover(doc, context["project"], context["generated_at"])
        doc.add_page_break()
        self._add_chapters(doc, context)

        doc.save(output_path)
        return output_path

    # ---- layout ----

    def _setup_page(self, doc: Document) -> None:
        section = doc.sections[0]
        section.page_width = Inches(8.27)   # A4
        section.page_height = Inches(11.69)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)

        # Running header: contractor branding + project code
        header = section.header
        hp = header.paragraphs[0]
        hp.text = ""
        run = hp.add_run(f"{self.contractor}  |  PROJECT CODE: {context_project_code(doc)}")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

        # Footer: Page X of Y + confidentiality
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = fp.add_run("Page ")
        run.font.size = Pt(8)
        fld1 = OxmlElement("w:fldSimple")
        fld1.set(qn("w:instr"), "PAGE")
        fp._p.append(fld1)
        run = fp.add_run(" of ")
        run.font.size = Pt(8)
        fld2 = OxmlElement("w:fldSimple")
        fld2.set(qn("w:instr"), "NUMPAGES")
        fp._p.append(fld2)
        p2 = footer.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p2.add_run("CONFIDENTIAL — Prepared for submission evaluation only.")
        r.font.size = Pt(7)
        r.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # ---- cover ----

    def _add_cover(self, doc: Document, project: Dict[str, Any], generated_at: str) -> None:
        for _ in range(6):
            doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run("TECHNICAL PROPOSAL")
        r.font.size = Pt(30)
        r.font.bold = True
        r.font.color.rgb = PRIMARY

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(project.get("name", "Project"))
        r.font.size = Pt(22)
        r.font.color.rgb = DARK

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(
            f"Client: {project.get('client', '—')}   |   "
            f"Tender Ref: {project.get('tender_reference', '—')}"
        )
        r.font.size = Pt(12)

        for _ in range(3):
            doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(self.contractor)
        r.font.size = Pt(14)
        r.font.bold = True

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(generated_at)
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # ---- chapters ----

    def _add_chapters(self, doc: Document, context: Dict[str, Any]) -> None:
        self._heading(doc, "1. Executive Summary")
        doc.add_paragraph(context["summary"])

        self._heading(doc, "2. Project Scope & Parameters")
        doc.add_paragraph(context["project"].get("scope") or "Standard scope of works per tender package.")

        self._heading(doc, "3. Value Engineering Proposals")
        self._ve_table(doc, context.get("ve_proposals", []))

        self._heading(doc, "4. SBC-304 Compliance Register")
        self._compliance_table(doc, context.get("compliance", []))

        self._heading(doc, "5. Engineering Method Statements")
        for m in context.get("method_statements", []):
            p = doc.add_paragraph()
            r = p.add_run(m["title"])
            r.font.bold = True
            doc.add_paragraph(m["content"])

        self._heading(doc, "6. Risk Register")
        self._risk_callouts(doc, context.get("risks", []))

        self._heading(doc, "7. Technical Evaluation")
        ev = context.get("evaluation", {})
        doc.add_paragraph(
            f"Overall Score: {ev.get('overall_score', 0)}/100 — "
            f"{'PASS' if ev.get('pass_fail') else 'FAIL'}. {ev.get('summary', '')}"
        )

    def _heading(self, doc: Document, text: str) -> None:
        h = doc.add_heading(level=1)
        r = h.add_run(text)
        r.font.color.rgb = PRIMARY
        r.font.size = Pt(16)

    # ---- tables ----

    def _ve_table(self, doc: Document, proposals: List[Dict[str, Any]]) -> None:
        if not proposals:
            doc.add_paragraph("No value-engineering candidates evaluated.")
            return
        table = doc.add_table(rows=1, cols=5)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["BOQ Item", "Proposed Alternative", "SBC Status", "Net Savings (SAR)", "Refs"]
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            _shade(cell, HEADER_BG)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    r.font.size = Pt(9)
        for v in proposals:
            row = table.add_row().cells
            row[0].text = str(v.get("boq_item", ""))
            row[1].text = str(v.get("proposed_alternative", ""))
            row[2].text = str(v.get("sbc_status", ""))
            row[3].text = f"{float(v.get('net_savings_sar') or 0):,.2f}"
            row[4].text = ", ".join(v.get("sbc_304_references", []) or [])
            for c in row:
                for p in c.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(8)

    def _compliance_table(self, doc: Document, compliance: List[Dict[str, Any]]) -> None:
        if not compliance:
            doc.add_paragraph("No compliance verdicts recorded.")
            return
        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        for i, h in enumerate(["Clause", "Requirement", "Status"]):
            cell = table.rows[0].cells[i]
            cell.text = h
            _shade(cell, HEADER_BG)
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    r.font.size = Pt(9)
        for c in compliance:
            row = table.add_row().cells
            row[0].text = str(c.get("clause_code", ""))
            row[1].text = str(c.get("requirement", ""))
            row[2].text = str(c.get("status", ""))
            for cell in row:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(8)

    # ---- callouts ----

    def _risk_callouts(self, doc: Document, risks: List[Dict[str, Any]]) -> None:
        if not risks:
            doc.add_paragraph("No material risks outstanding.")
            return
        for r in risks:
            severity = str(r.get("severity", "")).upper()
            is_warning = severity in ("CRITICAL", "HIGH")
            table = doc.add_table(rows=1, cols=1)
            table.style = "Table Grid"
            cell = table.rows[0].cells[0]
            _shade(cell, WARNING_BG if is_warning else NOTE_BG)
            label = "WARNING" if is_warning else "NOTE"
            cell.text = f"[{label}] {r.get('risk_id', 'RISK')} — {r.get('category', '')}\n{r.get('mitigation', '')}"
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)


def context_project_code(doc: Document) -> str:
    """Placeholder-safe project code (kept out of the main path)."""
    return "CT-2026"
