import unittest
from app.parsers.contract_risk_engine import ContractRiskEngine

class TestContractRiskEngine(unittest.TestCase):
    def test_14_day_notice_triggers_high_risk(self):
        clauses = [{"ref": "20.1", "text": "The Contractor must give notice of claim within 14 days."}]
        risks = ContractRiskEngine.analyze_clauses(clauses)
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]["severity"], "High")
        self.assertEqual(risks[0]["risk_type"], "Time-Bar Limit")

    def test_uncapped_ld_triggers_high_risk(self):
        clauses = [{"ref": "8.7", "text": "Delay damages are uncapped and without limit."}]
        risks = ContractRiskEngine.analyze_clauses(clauses)
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0]["severity"], "High")
        self.assertEqual(risks[0]["risk_type"], "Uncapped Liability")

    def test_safe_clause_ignored(self):
        # 28 days is the safe threshold
        clauses = [{"ref": "20.1", "text": "The Contractor must give notice of claim within 28 days."}]
        risks = ContractRiskEngine.analyze_clauses(clauses)
        self.assertEqual(len(risks), 0)

if __name__ == "__main__":
    unittest.main()
