"""
Document Ingestion Pipeline — verification tests
(register, classify, chunk, criteria extraction, RAG citations).
"""

import pytest

from app.parsers.criteria_extractor import extract_requirements
from app.parsers.document_classifier import classify_document, rank_criteria_candidates
from app.parsers.pdf_parser import extract_structural_specs

CRITERIA_TEXT = (
    "1. معايير التقييم الفني للمنافسة — تقييم العروض الفنية وفق المجموعات التالية.\n"
    "2. المجموعة الأولى: الخبرة الفنية للشركة — الوزن النسبي 30% من الدرجة الكلية.\n"
    "3. المجموعة الثانية: الكادر الفني المخصص — الوزن النسبي 25% من الدرجة الكلية.\n"
    "4. المجموعة الثالثة: المنهجية وبرنامج التنفيذ — الوزن النسبي 45% من الدرجة الكلية.\n"
    "5. شرط إلزامي: يجب تقديم ضمان ابتدائي بنسبة 1% من قيمة العرض، وإلا رفض العرض.\n"
    "6. أي عرض لا يجتاز الحد الأدنى 70% يُستبعد من المنافسة واستبعاد نهائي.\n"
    "7. Pass/Fail: تقديم شهادة الاشتراك في الغرفة التجارية سارية المفعول."
)

SPEC_TEXT = (
    "Structural concrete shall be Grade C40 with f'c = 40 MPa and maximum w/c 0.40.\n"
    "Exposure Class S2 applies to substructure. Rebar Grade 60 (fy 420 MPa).\n"
    "Minimum clear cover shall be 50 mm for cast against earth elements."
)

DRAWING_FILENAME = "Site-Plan-Rev2.dxf"


class TestDocumentClassifier:
    def test_classifies_evaluation_criteria(self):
        result = classify_document("معايير التقييم.pdf", CRITERIA_TEXT)
        assert result["category"] == "EVALUATION_CRITERIA", result
        assert result["confidence"] > 0

    def test_classifies_specifications(self):
        result = classify_document("Technical-Specs.pdf", SPEC_TEXT)
        assert result["category"] == "SPECIFICATIONS", result

    def test_drawings_by_filename(self):
        result = classify_document(DRAWING_FILENAME, "")
        assert result["category"] == "DRAWINGS", result

    def test_unknown_document_defaults_to_other(self):
        result = classify_document("random-notes.txt", "lorem ipsum dolor sit amet")
        assert result["category"] == "OTHER"

    def test_criteria_ranks_candidates(self):
        docs = [
            {"id": 1, "filename": "specs.pdf", "doc_category": "SPECIFICATIONS",
             "classification_confidence": 0.5, "text_sample": SPEC_TEXT},
            {"id": 2, "filename": "معايير التقييم.pdf", "doc_category": "EVALUATION_CRITERIA",
             "classification_confidence": 0.8, "text_sample": CRITERIA_TEXT},
            {"id": 3, "filename": "boq.xlsx", "doc_category": "BOQ",
             "classification_confidence": 0.4, "text_sample": "جدول الكميات"},
        ]
        ranked = rank_criteria_candidates(docs)
        assert ranked, "no candidates ranked"
        assert ranked[0]["id"] == 2, "criteria document should rank first"


class TestCriteriaExtractor:
    def test_extracts_weighted_criteria(self):
        reqs = extract_requirements(CRITERIA_TEXT, source_document_id=2)
        weighted = [r for r in reqs if r["requirement_type"] == "WEIGHTED"]
        assert weighted, "no weighted criteria extracted"
        weights = {r["weight"] for r in weighted}
        assert {30.0, 25.0, 45.0} <= weights, weights

    def test_extracts_mandatory_gates(self):
        reqs = extract_requirements(CRITERIA_TEXT, source_document_id=2)
        mandatory = [r for r in reqs if r["requirement_type"] == "MANDATORY"]
        assert mandatory, "no mandatory gates extracted"
        assert any("ضمان" in r["requirement_text"] or "guarantee" in r["requirement_text"].lower()
                   for r in mandatory) or any("Pass" in r["requirement_text"] for r in mandatory)

    def test_extracts_disqualification_conditions(self):
        reqs = extract_requirements(CRITERIA_TEXT, source_document_id=2)
        disqualifiers = [r for r in reqs if r["requirement_type"] == "DISQUALIFICATION"]
        assert disqualifiers, "disqualification condition not detected"
        assert any("70%" in r["requirement_text"] or "استبعد" in r["requirement_text"] or
                   "يُستبعد" in r["requirement_text"] for r in disqualifiers)

    def test_no_requirements_from_empty_text(self):
        assert extract_requirements("") == []


class TestStructuralSpecExtraction:
    def test_extracts_structural_parameters(self):
        import io, zlib
        content = SPEC_TEXT
        stream = zlib.compress(content.encode("latin-1"))
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>",
            b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        ]
        pdf = io.BytesIO()
        pdf.write(b"%PDF-1.4\n")
        offsets = []
        for i, obj in enumerate(objects, start=1):
            offsets.append(pdf.tell())
            pdf.write(f"{i} 0 obj\n".encode())
            pdf.write(obj + b"\nendobj\n")
        xref = pdf.tell()
        pdf.write(b"xref\n0 5\n0000000000 65535 f \n")
        for off in offsets:
            pdf.write(f"{off:010d} 00000 n \n".encode())
        pdf.write(b"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n")
        pdf.write(str(xref).encode() + b"\n%%EOF\n")

        from pathlib import Path
        path = Path("_spec_probe.pdf")
        path.write_bytes(pdf.getvalue())
        try:
            specs = extract_structural_specs(str(path))
            assert specs["fc_mpa"] == 40.0, specs
            assert specs["wc"] == 0.40
            assert specs["exposure_class"] == "S2"
            assert specs["fy_mpa"] == 420.0
            assert specs["cover_depth_mm"] == 50.0
            assert specs["placement_context"] == "CAST_AGAINST_EARTH"
        finally:
            path.unlink(missing_ok=True)