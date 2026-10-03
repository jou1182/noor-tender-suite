"""
RFP Clause Parser & Cross-Exam Suite — verification tests.

Covers:
  1. RfpClauseParser: strictness segmentation (Mandatory / Technical
     Specification / Commercial-Legal / Submittal Requirements), SBC standard
     extraction, penalty threshold detection, personnel requirements.
  2. CrossExamMatrixEngine: COMPLIANT / MINOR_DEVIATION / CRITICAL_GAP
     classification, compliance scoring, mandatory-gap counting, remediation.
  3. cross_exam_agent: state mutation with `rfp_compliance_matrix` and
     real-time SSE telemetry emission.
  4. Swarm telemetry bus round-trip.
"""

from app.agents.cross_exam_agent import cross_exam_agent
from app.parsers.cross_exam_matrix_engine import (
    COMPLIANT,
    MINOR_DEVIATION,
    CRITICAL_GAP,
    CrossExamMatrixEngine,
)
from app.parsers.rfp_clause_parser import RfpClauseParser
from app.core import swarm_telemetry

RFP_TEXT = (
    "MANDATORY GATE: All concrete works shall comply with SBC 304 structural requirements.\n"
    "MANDATORY GATE: Contractor must submit method statements and shop drawings for approval "
    "prior to commencement of works.\n"
    "MANDATORY GATE: Liquidated damages shall be capped at 10% of the contract value, "
    "payable at SAR 5,000 per day.\n"
    "TECHNICAL SPECIFICATION: Concrete mix design achieves 40 MPa with 0.38 water-cement ratio.\n"
    "COMMERCIAL TERMS: Payment terms are net 30 days with a 5% performance bond.\n"
    "SUBMITTAL: Provide shop drawings, method statements and as-built reports.\n"
    "MANDATORY GATE: Contractor shall provide a qualified project manager with 10+ years "
    "of experience.\n"
)

PROPOSAL_SECTIONS = [
    {
        "title": "Section 1 — Concrete Works",
        "text": (
            "We propose a C40 concrete mix complying with SBC 304. Water cement ratio "
            "0.38, 28-day compressive strength 42.5 MPa, chloride penetrability below "
            "1,000 coulombs."
        ),
    },
    {
        "title": "Section 2 — Quality & Submittals",
        "text": (
            "Method statements and shop drawings will be submitted for approval before "
            "commencement. Inspection and test plans follow ASTM C39."
        ),
    },
    {
        "title": "Section 3 — HSE",
        "text": (
            "HIRA risk register covers deep trench excavation with engineered shoring "
            "and confined-space permits."
        ),
    },
]


class TestRfpClauseParser:
    def test_parse_text_segments_strictness_categories(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        assert parsed["clauses"], "no clauses parsed"
        summary = parsed["segment_summary"]
        # The fixture must exercise all four target categories.
        assert "Mandatory" in summary, summary
        assert "Technical Specification" in summary, summary
        assert "Commercial/Legal" in summary, summary
        assert "Submittal Requirements" in summary, summary

    def test_sbc_standard_extraction(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        gates = parsed["compliance_gates"]
        assert "304" in gates["sbc_standards"], gates["sbc_standards"]
        assert gates["sbc_citations_total"] >= 1

    def test_penalty_threshold_detection(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        penalties = parsed["compliance_gates"]["penalty_thresholds"]
        assert penalties, "no penalty thresholds detected"
        gate = penalties[0]
        assert gate.get("detected") is True
        assert gate.get("rate") == 5000.0, gate
        assert gate.get("cap") == 10.0, gate

    def test_submittal_deliverable_detection(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        submittal = [c for c in parsed["clauses"] if c["strictness"] == "Submittal Requirements"]
        assert submittal, "no submittal clause classified"
        assert any("method statement" in c["text"].lower() for c in submittal)

    def test_personnel_requirements(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        target = next(c for c in parsed["clauses"] if "project manager" in c["text"].lower())
        assert target["personnel_requirements"], "personnel requirements not extracted"


class TestCrossExamMatrixEngine:
    def test_compliant_classification(self):
        clause = {
            "clause_id": 1, "ref": "RFP-C1", "clause_ref": "RFP-C1",
            "text": "Contractor must submit method statements and shop drawings for approval "
                    "prior to commencement of works.",
            "strictness": "Mandatory",
        }
        result = CrossExamMatrixEngine.compare([clause], PROPOSAL_SECTIONS)
        row = result["matrix"][0]
        assert row["status"] == COMPLIANT, row
        assert row["match_score"] > 0.45, row
        assert row["remediation"] == "", row

    def test_minor_deviation_classification(self):
        clause = {
            "clause_id": 2, "ref": "RFP-C2", "clause_ref": "RFP-C2",
            "text": "Concrete works shall comply with SBC 304 for all substructure elements.",
            "strictness": "Mandatory",
        }
        result = CrossExamMatrixEngine.compare([clause], PROPOSAL_SECTIONS)
        row = result["matrix"][0]
        assert row["status"] == MINOR_DEVIATION, row
        assert "MINOR DEVIATION" in row["remediation"], row

    def test_critical_gap_classification_without_proposal(self):
        clause = {
            "clause_id": 3, "ref": "RFP-C3", "clause_ref": "RFP-C3",
            "text": "Liquidated damages shall be capped at 10% of the contract value.",
            "strictness": "Mandatory",
        }
        # No proposal sections submitted -> requirement entirely unaddressed.
        result = CrossExamMatrixEngine.compare([clause], [])
        row = result["matrix"][0]
        assert row["status"] == CRITICAL_GAP, row
        assert row["matched_section"] is None
        assert "CRITICAL GAP" in row["remediation"], row

    def test_mandatory_gap_counting(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        result = CrossExamMatrixEngine.compare(parsed["clauses"], [])
        assert result["mandatory_gap_count"] >= 1, result["status_counts"]
        assert result["total_clauses"] == len(parsed["clauses"])
        assert sum(result["status_counts"].values()) == result["total_clauses"]

    def test_compliance_score_range(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        result = CrossExamMatrixEngine.compare(parsed["clauses"], PROPOSAL_SECTIONS)
        assert 0.0 <= result["compliance_score"] <= 100.0
        assert set(result["status_counts"].keys()) == {COMPLIANT, MINOR_DEVIATION, CRITICAL_GAP}

    def test_remediation_narratives_cover_all_statuses(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        mixed = CrossExamMatrixEngine.compare(parsed["clauses"], PROPOSAL_SECTIONS)
        # COMPLIANT rows carry no remediation; MINOR_DEVIATION rows carry narrative.
        for row in mixed["matrix"]:
            if row["status"] == MINOR_DEVIATION:
                assert "MINOR DEVIATION" in row["remediation"], row
            elif row["status"] == COMPLIANT:
                assert row["remediation"] == "", row
        # CRITICAL_GAP arises only when no proposal section addresses the clause.
        critical = CrossExamMatrixEngine.compare(parsed["clauses"], [])
        for row in critical["matrix"]:
            assert row["status"] == CRITICAL_GAP, row
            assert "CRITICAL GAP" in row["remediation"], row


class TestCrossExamAgent:
    def test_agent_mutates_state_with_matrix(self):
        parsed = RfpClauseParser.parse_text(RFP_TEXT)
        state = {
            "client_name": "TestClient",
            "rfp_output": {"clauses": parsed["clauses"]},
            "generated_proposal_output": PROPOSAL_SECTIONS,
        }
        emitted: list = []
        out = cross_exam_agent(state, emit=lambda ev: emitted.append(ev))
        assert "rfp_compliance_matrix" in out, "rfp_compliance_matrix missing from state mutation"
        matrix = out["rfp_compliance_matrix"]
        assert matrix["clause_count"] == len(parsed["clauses"])
        assert matrix["section_count"] == len(PROPOSAL_SECTIONS)
        assert set(matrix["status_counts"].keys()) == {COMPLIANT, MINOR_DEVIATION, CRITICAL_GAP}
        assert "matrix" in matrix and matrix["matrix"]

    def test_agent_refuses_to_invent_clauses_when_state_empty(self):
        import pytest
        from app.agents.errors import InsufficientInputError

        with pytest.raises(InsufficientInputError):
            cross_exam_agent({"client_name": "TestClient"})

    def test_agent_emits_realtime_telemetry(self):
        state = {
            "rfp_output": {"clauses": RfpClauseParser.parse_text(RFP_TEXT)["clauses"]},
            "generated_proposal_output": PROPOSAL_SECTIONS,
        }
        emitted: list = []
        cross_exam_agent(state, emit=lambda ev: emitted.append(ev))
        assert emitted, "no telemetry emitted"
        assert any("Cross-Exam Agent running" in e for e in emitted), emitted
        assert any("Cross-Exam Agent completed" in e for e in emitted), emitted


class TestSwarmTelemetryBus:
    def test_roundtrip_drain(self):
        swarm_telemetry.clear()
        swarm_telemetry.emit("Cross-Exam Agent completed — test telemetry")
        lines = swarm_telemetry.drain()
        assert lines, "buffer drain returned nothing"
        assert "Cross-Exam Agent completed" in lines[0]
        assert swarm_telemetry.drain() == []

    def test_agent_default_emit_reaches_bus(self):
        swarm_telemetry.clear()
        cross_exam_agent({"rfp_output": {"clauses": RfpClauseParser.parse_text(RFP_TEXT)["clauses"]}})
        lines = swarm_telemetry.drain()
        assert any("Cross-Exam Agent" in line for line in lines)
        swarm_telemetry.clear()