import unittest
from app.parsers.submittal_review_engine import SubmittalReviewEngine

class TestSubmittalReview(unittest.TestCase):
    def test_status_a_approval_for_perfect_compliance(self):
        submittal = {
            "material": "Grade 60 Steel Rebar",
            "parameters": [
                {"name": "Yield Strength", "required_value": 420, "submitted_value": 450, "operator": ">="},
                {"name": "Tensile Strength", "required_value": 620, "submitted_value": 630, "operator": ">="}
            ]
        }
        res = SubmittalReviewEngine.evaluate_submittal(submittal)
        self.assertEqual(res["review_status"], "CODE_A")
        self.assertEqual(res["review_action"], "Approved")
        self.assertEqual(res["discrepancies_found"], 0)

    def test_status_c_rejection_for_threshold_failure(self):
        submittal = {
            "material": "Fire-Rated Steel Door",
            "parameters": [
                {"name": "Fire Rating", "required_value": 120, "submitted_value": 90, "operator": ">="}
            ]
        }
        res = SubmittalReviewEngine.evaluate_submittal(submittal)
        self.assertEqual(res["review_status"], "CODE_C")
        self.assertEqual(res["review_action"], "Revise and Resubmit")
        self.assertEqual(res["discrepancies_found"], 1)

    def test_status_d_fatal_rejection_for_multiple_failures(self):
        submittal = {
            "material": "Substandard Masonry Block",
            "parameters": [
                {"name": "Compressive Strength", "required_value": 20, "submitted_value": 10, "operator": ">="},
                {"name": "Water Absorption", "required_value": 5, "submitted_value": 15, "operator": "<="},
                {"name": "Density", "required_value": 2000, "submitted_value": 1500, "operator": ">="}
            ]
        }
        res = SubmittalReviewEngine.evaluate_submittal(submittal)
        self.assertEqual(res["review_status"], "CODE_D")
        self.assertEqual(res["review_action"], "Rejected")
        self.assertEqual(res["discrepancies_found"], 3)
        self.assertTrue("FATAL" in res["technical_commentary"][0])

if __name__ == "__main__":
    unittest.main()
