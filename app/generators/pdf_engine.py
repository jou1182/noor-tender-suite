"""
PDF Document Renderer.

Renders the technical proposal to A4 PDF using reportlab's platypus pipeline.
Provides @page-equivalent layout (A4, margins), running headers/footers with
page counters, styled tables, and embedded vector status badges
(Pass / SBC Compliant / VE Recommended) drawn as colored circles.
"""

from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

PRIMARY = colors.HexColor("#0F766E")
DARK = colors.HexColor("#0F172A")
HEADER_BG = colors.HexColor("#0F172A")
LIGHT = colors.HexColor("#F1F5F9")


def _canvas_base():
    from reportlab.pdfgen import canvas as _canvas

    return _canvas.Canvas


class NumberedCanvas(_canvas_base()):
    """Canvas subclass injecting 'Page X of Y' + confidentiality into the footer.

    Subclasses reportlab's Canvas (keeping ``_doc`` as the internal PDFDocument)
    and draws the footer on every page via an overridden ``showPage``.
    """

    def __init__(self, *args, **kwargs):
        from reportlab.pdfgen import canvas as _canvas

        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._last_footer_page = -1

    def showPage(self):
        self._draw_footer()
        super(NumberedCanvas, self).showPage()

    def save(self):
        # Draw footer on the final page (idempotent guard against double draw).
        self._draw_footer()
        super(NumberedCanvas, self).save()

    def _draw_footer(self):
        if self._last_footer_page == self._pageNumber:
            return
        self._last_footer_page = self._pageNumber
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawCentredString(A4[0] / 2, 10 * mm, f"Page {self._pageNumber}")
        self.drawCentredString(A4[0] / 2, 6.5 * mm, "CONFIDENTIAL — Prepared for submission evaluation only.")
        self.restoreState()


def _badge_flow(text: str, color) -> List:
    """Vector badge as a small colored rounded box + text (platypus flow)."""
    from reportlab.platypus import Table as _T

    t = _T([[Paragraph(f'<font color="white"><b>{text}</b></font>', _get_badge_style())]], colWidths=[110])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


_badge_style_obj = None


def _get_badge_style():
    global _badge_style_obj
    if _badge_style_obj is None:
        _badge_style_obj = ParagraphStyle("Badge", fontName="Helvetica-Bold", fontSize=7.5, leading=9, alignment=TA_CENTER)
    return _badge_style_obj


class PdfProposalGenerator:
    """A4 PDF renderer for the technical proposal."""

    def __init__(self, contractor_name: str = "ConTech AI Contracting Co.") -> None:
        self.contractor = contractor_name
        self.styles = getSampleStyleSheet()
        self.body = ParagraphStyle(
            "Body", parent=self.styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=6
        )
        self.h1 = ParagraphStyle(
            "H1", parent=self.styles["Heading1"], fontSize=15, textColor=PRIMARY, spaceBefore=14, spaceAfter=8
        )
        self.cover_title = ParagraphStyle(
            "CoverTitle", parent=self.styles["Title"], fontSize=28, textColor=PRIMARY, alignment=TA_CENTER
        )
        self.cover_sub = ParagraphStyle(
            "CoverSub", parent=self.styles["Normal"], fontSize=13, alignment=TA_CENTER, spaceAfter=6
        )

    def generate(self, context: Dict[str, Any], output_path: str) -> str:
        doc = BaseDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=22 * mm,
            rightMargin=22 * mm,
            topMargin=24 * mm,
            bottomMargin=20 * mm,
        )
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main")
        doc.addPageTemplates(
            [PageTemplate(id="all", frames=[frame], onPage=self._on_page, onPageEnd=self._on_page_end)]
        )

        story: List[Any] = []
        story.extend(self._cover(context))
        story.append(Spacer(1, 18))
        story.extend(self._chapters(context))
        doc.build(story, canvasmaker=NumberedCanvas)
        return output_path

    # ---- page furniture ----

    def _on_page(self, canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(22 * mm, A4[0] / 2 if False else A4[1] - 12 * mm, f"{self.contractor}  |  PROJECT CODE: CT-2026")
        canvas.restoreState()

    def _on_page_end(self, canvas, doc) -> None:
        pass

    # ---- cover ----

    def _cover(self, context: Dict[str, Any]) -> List[Any]:
        p = context["project"]
        story: List[Any] = []
        for _ in range(5):
            story.append(Spacer(1, 16))
        story.append(Paragraph("TECHNICAL PROPOSAL", self.cover_title))
        story.append(Spacer(1, 10))
        story.append(Paragraph(p.get("name", "Project"), ParagraphStyle(
            "CoverName", parent=self.styles["Normal"], fontSize=20, textColor=DARK, alignment=TA_CENTER
        )))
        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f"Client: {p.get('client', '—')} &nbsp;|&nbsp; Tender Ref: {p.get('tender_reference', '—')}",
            self.cover_sub,
        ))
        story.append(Spacer(1, 30))
        story.append(Paragraph(self.contractor, ParagraphStyle(
            "CoverContractor", parent=self.styles["Normal"], fontSize=14, alignment=TA_CENTER, fontName="Helvetica-Bold"
        )))
        story.append(Paragraph(context.get("generated_at", ""), ParagraphStyle(
            "CoverDate", parent=self.styles["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#64748B")
        )))
        story.append(Spacer(1, 24))
        # Vector status badges on cover
        badge_row = Table(
            [
                [_badge_flow("SBC COMPLIANT", colors.HexColor("#059669")),
                 _badge_flow("VE RECOMMENDED", colors.HexColor("#0E7490")),
                 _badge_flow("PASS", colors.HexColor("#0F766E"))]
            ],
            colWidths=[110, 110, 110],
        )
        badge_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(badge_row)
        story.append(Spacer(1, 10))
        story.append(Paragraph("<pageBreak/>", self.body))
        return story

    # ---- chapters ----

    def _chapters(self, context: Dict[str, Any]) -> List[Any]:
        story: List[Any] = []

        story.append(Paragraph("1. Executive Summary", self.h1))
        story.append(Paragraph(context["summary"].replace("\n", "<br/>"), self.body))

        story.append(Paragraph("2. Project Scope & Parameters", self.h1))
        story.append(Paragraph(context["project"].get("scope") or "Standard scope of works per tender package.", self.body))

        story.append(Paragraph("3. Value Engineering Proposals", self.h1))
        story.extend(self._ve_table(context.get("ve_proposals", [])))

        story.append(Paragraph("4. SBC-304 Compliance Register", self.h1))
        story.extend(self._compliance_table(context.get("compliance", [])))

        story.append(Paragraph("5. Engineering Method Statements", self.h1))
        for m in context.get("method_statements", []):
            story.append(Paragraph(f"<b>{m['title']}</b>", self.body))
            story.append(Paragraph(m["content"], self.body))

        story.append(Paragraph("6. Risk Register", self.h1))
        story.extend(self._risk_callouts(context.get("risks", [])))

        story.append(Paragraph("7. Technical Evaluation", self.h1))
        ev = context.get("evaluation", {})
        story.append(Paragraph(
            f"Overall Score: <b>{ev.get('overall_score', 0)}/100</b> — "
            f"{'PASS' if ev.get('pass_fail') else 'FAIL'}. {ev.get('summary', '')}",
            self.body,
        ))
        return story

    def _ve_table(self, proposals: List[Dict[str, Any]]) -> List[Any]:
        if not proposals:
            return [Paragraph("No value-engineering candidates evaluated.", self.body)]
        data = [["BOQ Item", "Proposed Alternative", "SBC Status", "Net Savings (SAR)", "Refs"]]
        for v in proposals:
            data.append(
                [
                    str(v.get("boq_item", "")),
                    str(v.get("proposed_alternative", "")),
                    str(v.get("sbc_status", "")),
                    f"{float(v.get('net_savings_sar') or 0):,.2f}",
                    ", ".join(v.get("sbc_304_references", []) or []),
                ]
            )
        t = Table(data, colWidths=[70, 80, 45, 55, 70])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return [t]

    def _compliance_table(self, compliance: List[Dict[str, Any]]) -> List[Any]:
        if not compliance:
            return [Paragraph("No compliance verdicts recorded.", self.body)]
        data = [["Clause", "Requirement", "Status"]]
        for c in compliance:
            data.append([str(c.get("clause_code", "")), str(c.get("requirement", "")), str(c.get("status", ""))])
        t = Table(data, colWidths=[70, 220, 90])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return [t]

    def _risk_callouts(self, risks: List[Dict[str, Any]]) -> List[Any]:
        if not risks:
            return [Paragraph("No material risks outstanding.", self.body)]
        story: List[Any] = []
        for r in risks:
            severity = str(r.get("severity", "")).upper()
            color = colors.HexColor("#FEF3C7") if severity in ("CRITICAL", "HIGH") else colors.HexColor("#DBEAFE")
            label = "WARNING" if severity in ("CRITICAL", "HIGH") else "NOTE"
            t = Table(
                [[Paragraph(
                    f'<b>[{label}]</b> {r.get("risk_id", "RISK")} — {r.get("category", "")}<br/>{r.get("mitigation", "")}',
                    ParagraphStyle("Callout", fontSize=8.5, leading=11),
                )]],
                colWidths=[430],
            )
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), color),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 6))
        return story
