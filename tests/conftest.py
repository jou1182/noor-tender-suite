import pytest

SAMPLE_RFP_TEXT = (
    "Clause 1: All concrete works shall comply with SBC 304 for structural requirements.\n"
    "Clause 2: Contractor must submit method statements and shop drawings for approval prior to commencement.\n"
    "Clause 3: Liquidated damages shall be capped at 10% of the contract value.\n"
    "Clause 4: Technical specification: Concrete mix design achieves 40 MPa with 0.38 water-cement ratio.\n"
)


@pytest.fixture
def rfp_file(tmp_path):
    """A real, readable RFP text file (the repo's sample_data PDFs are 43-byte dummies)."""
    path = tmp_path / "rfp.txt"
    path.write_text(SAMPLE_RFP_TEXT, encoding="utf-8")
    return str(path)
