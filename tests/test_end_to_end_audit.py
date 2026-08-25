import unittest
from app.agents.graph import build_orchestrator

class TestEndToEndAudit(unittest.TestCase):
    def test_full_swarm_orchestration(self):
        orchestrator = build_orchestrator()
        initial_state = {"tender_id": 999}
        
        final_state = orchestrator.invoke(initial_state)
        
        self.assertIn("rfp_output", final_state)
        self.assertIn("boq_output", final_state)
        self.assertIn("methodology_output", final_state)
        self.assertIn("p6_output", final_state)
        self.assertIn("standards_output", final_state)
        self.assertIn("qaqc_output", final_state)
        self.assertIn("hse_output", final_state)
        self.assertIn("discrepancy_output", final_state)
        self.assertIn("red_team_output", final_state)
        self.assertIn("arbitrator_output", final_state)
        
        self.assertEqual(final_state["arbitrator_output"]["final_score"], 82.5)
        self.assertEqual(final_state["arbitrator_output"]["status"], "APPROVED")

if __name__ == '__main__':
    unittest.main()
