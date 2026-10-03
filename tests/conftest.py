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


# Task 5 is orphaned (no logic), task 3 has a -16h (-2d) lag, task 4 has 480h (60d) float and a
# mandatory-finish constraint, tasks 1-3 are critical (float 0).
SAMPLE_XER_TEXT = (
    "%T\tTASK\n"
    "%F\ttask_id\ttask_name\ttotal_float_hr_cnt\tremain_drtn_hr_cnt\tcstr_type\ttask_type\tstatus_code\n"
    "%R\t1\tDesign\t0\t240\t\tTT_Task\tTK_NotStart\n"
    "%R\t2\tProcure\t0\t480\t\tTT_Task\tTK_NotStart\n"
    "%R\t3\tBuild\t0\t960\t\tTT_Task\tTK_NotStart\n"
    "%R\t4\tLandscape\t480\t160\tCS_MANDFIN\tTT_Task\tTK_NotStart\n"
    "%R\t5\tOrphan\t16\t80\t\tTT_Task\tTK_NotStart\n"
    "%R\t6\tDone\t0\t0\t\tTT_Task\tTK_Complete\n"
    "%T\tTASKPRED\n"
    "%F\ttask_id\tpred_task_id\tlag_hr_cnt\n"
    "%R\t2\t1\t0\n"
    "%R\t3\t2\t-16\n"
    "%R\t4\t3\t0\n"
)


@pytest.fixture
def xer_file(tmp_path):
    path = tmp_path / "schedule.xer"
    path.write_text(SAMPLE_XER_TEXT, encoding="utf-8")
    return str(path)
