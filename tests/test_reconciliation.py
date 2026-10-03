import unittest
from app.parsers.reconciliation_engine import ReconciliationEngine
from app.agents.cross_exam_agent import cross_exam_agent

class TestReconciliationEngine(unittest.TestCase):
    def test_variance_calculation_high_severity(self):
        rates = {"Excavation": 500} # 500 units/day
        boq = {"Excavation": 10000} # 10000 units total -> expected 20 days
        p6 = {"Excavation": 12} # Scheduled 12 days -> variance = 8/20 = 40%

        discrepancies = ReconciliationEngine.calculate_variances(rates, boq, p6)
        
        self.assertEqual(len(discrepancies), 1)
        self.assertEqual(discrepancies[0]["activity"], "Excavation")
        self.assertEqual(discrepancies[0]["variance_percent"], 40.0)
        self.assertEqual(discrepancies[0]["severity"], "High")
        self.assertIn("exceeds 10% threshold", discrepancies[0]["conflict"])

    def test_variance_calculation_no_flag_under_threshold(self):
        rates = {"Concrete": 100} # expected 10 days
        boq = {"Concrete": 1000} 
        p6 = {"Concrete": 10} # 0 variance

        discrepancies = ReconciliationEngine.calculate_variances(rates, boq, p6)
        self.assertEqual(len(discrepancies), 0)

    def test_cross_exam_agent_reports_no_invented_discrepancies(self):
        clauses = [{"clause_id": 1, "ref": "RFP-C1", "text": "All works shall comply with SBC 304.",
                    "strictness": "Mandatory"}]
        result = cross_exam_agent({"rfp_output": {"clauses": clauses}})
        # No BOQ/rates/schedule maps in state -> no fabricated "Excavation" variance.
        self.assertEqual(result["discrepancy_output"]["discrepancies"], [])

    def test_cross_exam_agent_uses_real_state_maps(self):
        clauses = [{"clause_id": 1, "ref": "RFP-C1", "text": "All works shall comply with SBC 304.",
                    "strictness": "Mandatory"}]
        state = {
            "rfp_output": {"clauses": clauses},
            "generated_proposal_output": [{"boq_item": "Excavation", "productivity_rate": 500,
                                           "method_statement_text": "Excavation per SBC 304."}],
            "boq_output": {"quantities": {"Excavation": 10000}},
            "p6_output": {"activity_durations": {"Excavation": 12}},
        }
        d = cross_exam_agent(state)["discrepancy_output"]["discrepancies"]
        self.assertEqual(d[0]["variance_percent"], 40.0)

if __name__ == "__main__":
    unittest.main()
