import unittest
from app.services.proposal_generator import ProposalGeneratorService

class TestProposalGenerator(unittest.TestCase):
    def test_concrete_generation(self):
        result = ProposalGeneratorService.generate_method_statement("Reinforced Concrete Slab", "Specs XYZ")
        self.assertIn("SBC 304", result["method_statement_text"])
        self.assertTrue(len(result["crew_composition"]) > 0)
        self.assertTrue(len(result["equipment_allocation"]) > 0)
        self.assertGreater(result["productivity_rate"], 0.0)

    def test_earthworks_generation(self):
        result = ProposalGeneratorService.generate_method_statement("Site Excavation Work", "Specs XYZ")
        self.assertIn("SBC 303", result["method_statement_text"])
        self.assertIn("Excavator", " ".join(result["equipment_allocation"]))
        
    def test_build_full_proposal(self):
        results = ProposalGeneratorService.build_full_proposal(["Concrete Foundation", "Excavation"], "Specs")
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["boq_item"], "Concrete Foundation")

if __name__ == "__main__":
    unittest.main()
