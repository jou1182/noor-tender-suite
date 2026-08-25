"""
Proposal Evaluation Test Suite.

Asserts that intentional omissions in the team's draft proposal (missing QA
plan, absent engineer CV, unaddressed concrete method statement) are detected
and scored with appropriate penalty deductions.
"""

import unittest

from app.agents.swarm_config import evaluation_agent_node
from app.parsers.proposal_evaluator import BidVsRFPEvaluator


class TestBidVsRFPEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = BidVsRFPEvaluator()

    def test_complete_proposal_scores_high(self):
        proposal = (
            "1. Quality Plan: project QA/QC organization with inspection and test plans.\n"
            "2. Project Manager: 12 years of relevant experience, CV attached.\n"
            "3. Method Statement: concrete pouring and curing per SBC-304.\n"
            "4. Commercial Registration and contractor classification certificates attached.\n"
            "5. Construction Schedule: 22-month baseline programme."
        )
        scorecard = self.evaluator.evaluate(proposal)
        self.assertGreaterEqual(scorecard.total_score, 80.0)
        self.assertEqual(scorecard.clauses_addressed, 5)

    def test_missing_qa_plan_detected_with_penalty(self):
        proposal = (
            "1. Method Statement: concrete pouring and curing per SBC-304.\n"
            "2. Project Manager: 12 years of experience, CV attached.\n"
            "3. Construction Schedule: 22-month baseline programme."
        )
        scorecard = self.evaluator.evaluate(proposal)
        # QA plan mandate (M-1) is unaddressed.
        self.assertLess(scorecard.total_score, 80.0)
        qa_gap = next(g for g in scorecard.gaps if g.clause_id == "M-1")
        self.assertEqual(qa_gap.gap_type, "MISSING_ATTACHMENT")
        self.assertIn("quality_plan", qa_gap.description)
        self.assertGreater(qa_gap.penalty_points, 0.0)

    def test_wrong_engineer_experience_flagged(self):
        # Proposal claims only 3 years experience -> keyword overlap below threshold.
        proposal = (
            "1. Quality Plan: QA/QC organization with inspection plans.\n"
            "2. Project Manager: 3 years of experience.\n"
            "3. Method Statement: concrete works per SBC-304.\n"
            "4. Commercial Registration certificate attached.\n"
            "5. Construction Schedule: 24-month programme."
        )
        scorecard = self.evaluator.evaluate(proposal)
        match = next(m for m in scorecard.matches if m.clause_id == "M-2")
        self.assertFalse(match.addressed)
        self.assertEqual(match.depth, "NONE")

    def test_gap_matrix_lists_all_omissions(self):
        proposal = "General mobilization and site setup only."
        scorecard = self.evaluator.evaluate(proposal)
        self.assertEqual(len(scorecard.gaps), len(self.evaluator.mandates))
        gap_types = {g.gap_type for g in scorecard.gaps}
        self.assertIn("UNADDRESSED", gap_types)


class TestEvaluationAgentNode(unittest.TestCase):
    def test_node_mutates_state(self):
        state = {
            "rfp_text": "",
            "proposal_draft_text": (
                "1. Quality Plan: QA/QC organization with inspection and test plans.\n"
                "2. Project Manager: 15 years of experience, CV attached.\n"
                "3. Method Statement: concrete works per SBC-304.\n"
                "4. Commercial Registration and classification certificates attached.\n"
                "5. Construction Schedule: 22-month baseline programme."
            ),
        }
        out = evaluation_agent_node(state)
        self.assertIn("proposal_evaluation", out)
        self.assertIn("compliance_matrix", out)
        self.assertGreater(out["proposal_evaluation"]["total_score"], 0.0)


if __name__ == "__main__":
    unittest.main()
