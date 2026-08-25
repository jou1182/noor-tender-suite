"""
Parsing Pipeline Test Suite.

Builds mock Excel (.xlsx) and PDF (.pdf) buffers in memory and validates:

  1. Excel BOQ extraction — header detection, multi-sheet, merged headers,
     summary-row exclusion, 100% row accuracy.
  2. PDF spec extraction — structural parameters (f'c, w/c, exposure, steel
     grade, cover) via pypdf + deterministic rules.
  3. Normalizer — BOQLineItem / ConcreteSpecInput model validation and
     VE-ready mapping into ValueEngineeringEngine.generate_ve_matrix().
"""

import io
import sys
import unittest
from pathlib import Path

from app.parsers.document_normalizer import BOQLineItem, ConcreteSpecInput, DocumentNormalizer
from app.parsers.excel_parser import detect_header_row, extract_boq_from_buffer
from app.parsers.pdf_parser import extract_structural_specs, extract_spec_sections
from app.parsers.value_engineering_engine import ValueEngineeringEngine


def make_boq_buffer() -> bytes:
    """Build a multi-sheet .xlsx in memory with a summary row to exclude."""
    from openpyxl import Workbook

    wb = Workbook()

    # Sheet 1: clean BOQ with merged header cells.
    ws = wb.active
    ws.title = "BOQ"
    ws.merge_cells("A1:B1")
    ws["A1"] = "Item"
    ws["C1"] = "Unit"
    ws["D1"] = "Quantity"
    ws["E1"] = "Unit Rate"
    ws["F1"] = "Total Amount"
    rows = [
        ("1", "Raft Foundation C35", "m3", 1200, 620, 744000),
        ("2", "Grade 60 Steel Rebar", "kg", 8500, 3.0, 25500),
        ("3", "Subtotal — Works", "", None, None, 769500),
        ("4", "Slab on Grade Lean Fill", "m3", 800, 580, 464000),
    ]
    for r, row in enumerate(rows, start=2):
        for c, val in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=val)

    # Sheet 2: alternate header spellings (per-unit price, qty.).
    ws2 = wb.create_sheet("Pricing")
    ws2.append(["Item No", "Description", "UOM", "Qty.", "Price/Unit", "Amount"])
    ws2.append(["B-1", "Pozzolanic Cement Blend", "ton", 500, 700, 350000])
    ws2.append(["B-2", "Grand Total", "", "", "", 350000])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_spec_pdf_buffer() -> bytes:
    """Build a minimal single-page PDF containing structural spec text."""
    content = (
        "3.1 Concrete Materials\n"
        "Structural concrete shall be Grade C35 with f'c = 35 MPa and maximum w/c 0.40.\n"
        "Exposure Class S2 (moderate sulfate) applies to all substructure elements.\n"
        "Reinforcement shall be Grade 60 (fy 420 MPa) deformed bars.\n"
        "Minimum clear cover shall be 50 mm for concrete cast against earth.\n"
        "4.0 Placement\n"
        "All concrete placed directly on grade shall be considered cast against earth."
    )
    # Minimal valid PDF with a Flate-compressed content stream.
    import zlib

    stream = zlib.compress(content.encode("latin-1"))
    objects = []
    objects.append(
        b"<< /Type /Catalog /Pages 2 0 R >>"
    )
    objects.append(
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
    )
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = io.BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{i} 0 obj\n".encode())
        pdf.write(obj + b"\n")
        pdf.write(b"endobj\n")
    xref_pos = pdf.tell()
    pdf.write(b"xref\n0 6\n")
    pdf.write(b"0000000000 65535 f \n")
    for off in offsets:
        pdf.write(f"{off:010d} 00000 n \n".encode())
    pdf.write(b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n")
    pdf.write(str(xref_pos).encode() + b"\n%%EOF\n")
    return pdf.getvalue()


class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.buffer = make_boq_buffer()

    def test_header_detection(self):
        from openpyxl import load_workbook

        wb = load_workbook(io.BytesIO(self.buffer), read_only=True, data_only=True)
        ws = wb["BOQ"]
        self.assertEqual(detect_header_row(ws), 0)
        wb.close()

    def test_extracts_all_data_rows_excluding_summary(self):
        rows = extract_boq_from_buffer(self.buffer)
        # 3 data rows: sheet1 (raft, rebar, slab) + sheet2 (pozzolanic). Summary rows excluded.
        self.assertEqual(len(rows), 4)
        descriptions = [r["description"] for r in rows]
        self.assertIn("Raft Foundation C35", descriptions)
        self.assertIn("Grade 60 Steel Rebar", descriptions)
        self.assertIn("Slab on Grade Lean Fill", descriptions)
        self.assertNotIn("Subtotal — Works", descriptions)
        self.assertNotIn("Grand Total", descriptions)

    def test_normalized_numbers_and_total_fallback(self):
        rows = extract_boq_from_buffer(self.buffer)
        raft = next(r for r in rows if r["description"] == "Raft Foundation C35")
        self.assertEqual(raft["qty"], 1200)
        self.assertEqual(raft["unit_rate"], 620)
        self.assertEqual(raft["total_amount"], 744000)


class TestPdfParser(unittest.TestCase):
    def setUp(self):
        self.buffer = make_spec_pdf_buffer()
        self.path = Path(__file__).parent / "_mock_spec.pdf"
        self.path.write_bytes(self.buffer)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_extracts_spec_sections(self):
        sections = extract_spec_sections(str(self.path))
        self.assertTrue(sections, "no sections extracted")
        joined = " ".join(s["content"] for s in sections)
        self.assertIn("35 MPa", joined)
        self.assertIn("Exposure Class S2", joined)

    def test_extracts_structural_parameters(self):
        specs = extract_structural_specs(str(self.path))
        self.assertEqual(specs["fc_mpa"], 35.0)
        self.assertEqual(specs["wc"], 0.40)
        self.assertEqual(specs["exposure_class"], "S2")
        self.assertEqual(specs["fy_mpa"], 420.0)
        self.assertEqual(specs["cover_depth_mm"], 50.0)
        self.assertEqual(specs["placement_context"], "CAST_AGAINST_EARTH")


class TestDocumentNormalizer(unittest.TestCase):
    def test_boq_line_item_validation(self):
        item = BOQLineItem(
            item_no="1",
            description="Raft Foundation C35",
            unit="m3",
            qty="1,200",
            unit_rate=620,
            total_amount="744000",
        )
        self.assertEqual(item.qty, 1200.0)
        self.assertEqual(item.total_amount, 744000.0)

    def test_concrete_spec_input_validation(self):
        spec = ConcreteSpecInput(
            fc_mpa=35.0, wc=0.40, exposure_class="s2",
            fy_mpa=420.0, cover_depth_mm=50.0, placement_context="cast against earth",
        )
        self.assertEqual(spec.exposure_class, "S2")
        self.assertEqual(spec.placement_context, "CAST_AGAINST_EARTH")

    def test_normalize_excel_rows(self):
        rows = extract_boq_from_buffer(make_boq_buffer())
        items = DocumentNormalizer.normalize_boq_rows(rows)
        self.assertEqual(len(items), 4)
        self.assertIsInstance(items[0], BOQLineItem)

    def test_feeds_ve_engine(self):
        rows = extract_boq_from_buffer(make_boq_buffer())
        items = DocumentNormalizer.normalize_boq_rows(rows)
        ve_inputs = [DocumentNormalizer.boq_to_ve_input(i) for i in items]
        cards = ValueEngineeringEngine.generate_ve_matrix(ve_inputs)
        self.assertIsInstance(cards, list)
        for card in cards:
            self.assertTrue(hasattr(card, "sbc_status"))
            self.assertIn(card.sbc_status, ("COMPLIANT", "BLOCKED"))

    def test_full_pipeline_buffer_to_ve(self):
        boq_buffer = make_boq_buffer()
        spec_path = Path(__file__).parent / "_mock_spec.pdf"
        spec_path.write_bytes(make_spec_pdf_buffer())
        try:
            ve_items = DocumentNormalizer.build_ve_items(
                workbook_buffer=boq_buffer, pdf_path=str(spec_path)
            )
            self.assertTrue(ve_items)
            cards = ValueEngineeringEngine.generate_ve_matrix(ve_items)
            self.assertTrue(cards)
        finally:
            spec_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
