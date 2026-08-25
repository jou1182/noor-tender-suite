import unittest
from app.parsers.rfq_package_engine import RfqPackageEngine

class TestRfqProcurement(unittest.TestCase):
    def test_trade_clustering_logic(self):
        boq = [
            {"description": "Mass excavation for basement", "qty": 100},
            {"description": "Install concrete footings", "qty": 50},
            {"description": "PVC Drainage pipe 150mm", "qty": 200},
            {"description": "General site office setup and mobilization", "qty": 1}
        ]
        
        clusters = RfqPackageEngine.cluster_boq_items(boq)
        
        # Verify accurate regex mappings onto CSI divisions
        self.assertIn("Earthworks (CSI 31)", clusters)
        self.assertIn("Concrete (CSI 03)", clusters)
        self.assertIn("Piping & Utilities (CSI 33)", clusters)
        self.assertIn("General Requirements", clusters)
        
        self.assertEqual(len(clusters["Earthworks (CSI 31)"]), 1)
        self.assertEqual(len(clusters["General Requirements"]), 1)

    def test_vendor_bid_normalization_and_defensive_penalty(self):
        budget = 100000.0
        quotes = [
            # A submits a complete 100% scope package at 95k
            {"vendor_name": "Vendor A", "bid_amount": 95000.0, "scope_coverage_pct": 100.0},
            # B submits what looks like a cheaper bid at 90k, but deliberately omitted 10% of the scope
            {"vendor_name": "Vendor B", "bid_amount": 90000.0, "scope_coverage_pct": 90.0} 
        ]
        
        evaluations = RfqPackageEngine.normalize_vendor_bids(budget, quotes)
        
        # Expected Math:
        # Vendor A: Normalized = 95,000 (Optimal)
        # Vendor B: Normalized = 90,000 + (100,000 * 10% missed scope * 1.1 risk premium) = 90,000 + 11,000 = 101,000
        
        vendor_a = next(v for v in evaluations if v["vendor_name"] == "Vendor A")
        vendor_b = next(v for v in evaluations if v["vendor_name"] == "Vendor B")
        
        self.assertEqual(vendor_a["normalized_bid"], 95000.0)
        self.assertEqual(vendor_b["normalized_bid"], 101000.0)
        
        # The algorithm correctly protected the company from the deceptively 'cheap' incomplete quote
        self.assertTrue(vendor_a["is_optimal"])
        self.assertFalse(vendor_b["is_optimal"])

if __name__ == "__main__":
    unittest.main()
