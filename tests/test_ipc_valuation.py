import unittest
from app.parsers.ipc_valuation_engine import IpcValuationEngine

class TestIpcValuation(unittest.TestCase):
    def test_standard_ipc_mathematics(self):
        data = {
            "contract_value": 100000,
            "previous_gross": 0,
            "previous_net": 0,
            "current_work_done": 10000,
            "materials_on_site": 0,
            "advance_payment_total": 0,
            "advance_recovered_previously": 0,
            "advance_recovery_rate": 0.0,
            "retention_rate": 0.10,
            "retention_cap_rate": 0.05,
            "liquidated_damages": 0.0
        }
        res = IpcValuationEngine.calculate_ipc(data)
        
        self.assertEqual(res["cumulative_gross"], 10000)
        self.assertEqual(res["actual_retention"], 1000) # 10% of 10,000
        self.assertEqual(res["amount_due_pre_vat"], 9000)
        self.assertEqual(res["vat_amount"], 1350) # 15% of 9,000
        self.assertEqual(res["total_certified_payment"], 10350)

    def test_retention_cap_limit_enforcement(self):
        data = {
            "contract_value": 100000,
            "previous_gross": 45000,
            "previous_net": 40000,
            "current_work_done": 20000,
            "materials_on_site": 0,
            "advance_payment_total": 0,
            "advance_recovered_previously": 0,
            "advance_recovery_rate": 0.0,
            "retention_rate": 0.10,
            "retention_cap_rate": 0.05, # Max retention capped at 5,000 strictly
            "liquidated_damages": 0.0
        }
        res = IpcValuationEngine.calculate_ipc(data)
        
        self.assertEqual(res["cumulative_gross"], 65000)
        # Without cap, retention would be 6,500. It MUST be capped at 5,000.
        self.assertEqual(res["actual_retention"], 5000)

    def test_advance_payment_recovery_limit_enforcement(self):
        data = {
            "contract_value": 100000,
            "previous_gross": 0,
            "previous_net": 0,
            "current_work_done": 50000,
            "materials_on_site": 0,
            "advance_payment_total": 10000,
            "advance_recovered_previously": 8000,
            "advance_recovery_rate": 0.10, # 10% of 50,000 = 5,000
            "retention_rate": 0.0,
            "retention_cap_rate": 0.05,
            "liquidated_damages": 0.0
        }
        res = IpcValuationEngine.calculate_ipc(data)
        
        # Max recovery should strictly be limited to 2,000 to prevent negative balance
        self.assertEqual(res["actual_recovery"], 2000)
        self.assertEqual(res["advance_payment_balance"], 0.0)

if __name__ == "__main__":
    unittest.main()
