import unittest
from app.services.feedback_engine import FeedbackEngine

class TestFeedbackEngine(unittest.TestCase):
    def setUp(self):
        # Establish isolated in-memory Qdrant core
        self.engine = FeedbackEngine(use_memory=True)
        
    def test_record_and_retrieve_disqualifications(self):
        # 1. Record a WON tender (Should be explicitly ignored by risk retriever)
        self.engine.record_outcome("T-1", "ClientA", "Won", "Excellent methodology.")
        
        # 2. Record a LOST tender (Should be retrieved)
        self.engine.record_outcome("T-2", "ClientA", "Lost", "Price was too high.")
        
        # 3. Record a DISQUALIFIED tender (Should be retrieved)
        self.engine.record_outcome("T-3", "ClientA", "Disqualified", "Missing local content.")
        
        # 4. Fetch the ClientA risks
        risks = self.engine.retrieve_historical_risks("clienta")
        
        # Validate that only negative outcomes (Lost/Disqualified) were fetched
        self.assertEqual(len(risks), 2)
        
        outcomes = [r["outcome"] for r in risks]
        self.assertIn("Lost", outcomes)
        self.assertIn("Disqualified", outcomes)
        self.assertNotIn("Won", outcomes)
        
        # Validate specific payloads survived the vector space
        lessons = [r["lesson_learned"] for r in risks]
        self.assertIn("Missing local content.", lessons)

if __name__ == "__main__":
    unittest.main()
