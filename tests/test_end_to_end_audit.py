import os
import unittest

from app.agents.arbitrator_agent import arbitrator_agent
from app.agents.errors import InsufficientInputError
from app.agents.graph import build_orchestrator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestEndToEndAudit(unittest.TestCase):
    def test_empty_input_fails_loudly_instead_of_fabricating(self):
        with self.assertRaises(InsufficientInputError):
            build_orchestrator().invoke({"tender_id": 999})

    def test_full_swarm_orchestration_on_real_sample(self):
        from tests.conftest import SAMPLE_XER_TEXT
        import tempfile
        from tests.conftest import SAMPLE_RFP_TEXT

        with tempfile.TemporaryDirectory() as tmp:
            rfp = os.path.join(tmp, "rfp.txt")
            with open(rfp, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE_RFP_TEXT)
            xer = os.path.join(tmp, "schedule.xer")
            with open(xer, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE_XER_TEXT)
            final_state = build_orchestrator().invoke(
                {"tender_id": 999, "rfp_documents": [rfp], "schedule_file": xer}
            )
        for key in ("rfp_output", "boq_output", "methodology_output", "p6_output", "standards_output",
                    "qaqc_output", "hse_output", "discrepancy_output", "red_team_output", "arbitrator_output"):
            self.assertIn(key, final_state)

        evaluation = final_state["tender_evaluation"]
        arb = final_state["arbitrator_output"]
        self.assertEqual(arb["final_score"], evaluation["overall_score"])
        self.assertEqual(arb["status"], "APPROVED" if evaluation["pass_fail"] else "REJECTED")

    def test_arbitrator_requires_evaluation(self):
        with self.assertRaises(InsufficientInputError):
            arbitrator_agent({})


if __name__ == '__main__':
    unittest.main()
