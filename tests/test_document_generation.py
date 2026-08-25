"""
Document Generation Test Suite.

Asserts that both PDF and DOCX proposal artifacts are generated without
layout corruption and contain all mandatory chapters.
"""

import os
import tempfile
import unittest
from pathlib import Path

from app.generators.docx_engine import DocxProposalGenerator
from app.generators.narrative_engine import ProposalNarrativeEngine
from app.generators.pdf_engine import PdfProposalGenerator

MOCK_PROJECT = {
    "name": "NEOM Capital Works Package",
    "client": "Saudi Aramco",
    "tender_reference": "RFQ-2026-0114",
    "scope": "Structural concrete foundations, earthworks and steel reinforcement works per SBC-304.",
}

MOCK_VE = [
    {
        "boq_item": "Raft Foundation C35",
        "proposed_alternative": "C35 GGBFS 50% (Slag-Blended Cement)",
        "sbc_status": "COMPLIANT",
        "net_savings_sar": 59520.0,
        "technical_justification": "Slag replacement lowers cost while meeting SBC 304 strength.",
        "sbc_304_references": ["SBC 304 Table 4.3.1", "SBC 304 Sec 7.7"],
    },
    {
        "boq_item": "Slab on Grade",
        "proposed_alternative": "Lean Concrete (Low-Cement Fill)",
        "sbc_status": "BLOCKED",
        "net_savings_sar": 0.0,
        "technical_justification": "NON-COMPLIANT with SBC 304: f'c below minimum.",
        "sbc_304_references": ["SBC 304 Table 4.3.1"],
    },
]

MOCK_COMPLIANCE = [
    {
        "clause_code": "SBC-304 §5.2",
        "requirement": "Concrete compressive strength f'c >= minimum",
        "status": "COMPLIANT",
        "gap_analysis": "C35 mix verified at 42.5 MPa.",
    },
    {
        "clause_code": "SBC-304 §7.7",
        "requirement": "Minimum cover per placement",
        "status": "COMPLIANT_WITH_DEVIATION",
        "gap_analysis": "Cover 40mm vs 50mm for cast-against-earth.",
    },
]

MOCK_RISKS = [
    {
        "risk_id": "TEV-RISK-1",
        "category": "Structural & Code Compliance",
        "severity": "CRITICAL",
        "mitigation": "Re-certify S4 exposure mix before submission.",
    }
]

MOCK_EVALUATION = {
    "overall_score": 82.5,
    "pass_fail": True,
    "summary": "Technical evaluation PASSED at 82.5/100 (gate >= 70%).",
}

MANDATORY_CHAPTERS = [
    "Executive Summary",
    "Project Scope",
    "Value Engineering",
    "SBC-304 Compliance",
    "Method Statements",
    "Risk Register",
    "Technical Evaluation",
]


def build_context() -> dict:
    engine = ProposalNarrativeEngine()
    return engine.build_context(
        project=MOCK_PROJECT,
        ve_proposals=MOCK_VE,
        compliance=MOCK_COMPLIANCE,
        risks=MOCK_RISKS,
        evaluation=MOCK_EVALUATION,
    )


class TestNarrativeEngine(unittest.TestCase):
    def test_render_narrative_contains_all_chapters(self):
        narrative = ProposalNarrativeEngine().render_narrative(build_context())
        lower = narrative.lower()
        for chapter in MANDATORY_CHAPTERS:
            self.assertIn(chapter.lower(), lower, f"missing chapter: {chapter}")

    def test_ve_justification_badge(self):
        engine = ProposalNarrativeEngine()
        compliant = engine.ve_justification(MOCK_VE[0])
        blocked = engine.ve_justification(MOCK_VE[1])
        self.assertIn("[SBC COMPLIANT]", compliant)
        self.assertIn("[BLOCKED BY SBC 304]", blocked)
        self.assertIn("SBC 304 Table 4.3.1", compliant)

    def test_method_statements_from_scope(self):
        engine = ProposalNarrativeEngine()
        statements = engine.build_method_statements(MOCK_PROJECT)
        titles = [m["title"] for m in statements]
        self.assertIn("Structural Concrete Method Statement", titles)
        self.assertIn("Earthworks & Excavation Method Statement", titles)


class TestDocxGenerator(unittest.TestCase):
    def test_generates_docx_with_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "proposal.docx")
            DocxProposalGenerator().generate(build_context(), path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 2000)

            from docx import Document

            doc = Document(path)
            text = "\n".join(p.text for p in doc.paragraphs)
            # Chapter headings are paragraph runs.
            for chapter in MANDATORY_CHAPTERS:
                self.assertIn(chapter, text, f"missing chapter in DOCX: {chapter}")

            # Styled tables present: VE + compliance.
            self.assertGreaterEqual(len(doc.tables), 2)
            # Cover page: contractor + client.
            self.assertIn("TECHNICAL PROPOSAL", text)
            self.assertIn("Saudi Aramco", text)

    def test_docx_has_footer_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "proposal.docx")
            DocxProposalGenerator().generate(build_context(), path)
            from docx import Document

            doc = Document(path)
            footer_text = "\n".join(p.text for p in doc.sections[0].footer.paragraphs)
            self.assertIn("CONFIDENTIAL", footer_text)


class TestPdfGenerator(unittest.TestCase):
    def test_generates_pdf_with_chapters(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "proposal.pdf")
            PdfProposalGenerator().generate(build_context(), path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 3000)

            # Validate PDF structure via pypdf.
            from pypdf import PdfReader

            reader = PdfReader(path)
            self.assertGreaterEqual(len(reader.pages), 1)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            for chapter in MANDATORY_CHAPTERS:
                self.assertIn(chapter, text, f"missing chapter in PDF: {chapter}")
            self.assertIn("TECHNICAL PROPOSAL", text)

    def test_pdf_contains_badges(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "proposal.pdf")
            PdfProposalGenerator().generate(build_context(), path)
            from pypdf import PdfReader

            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            self.assertIn("SBC COMPLIANT", text)
            self.assertIn("VE RECOMMENDED", text)


if __name__ == "__main__":
    unittest.main()
