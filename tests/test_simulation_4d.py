import unittest
from app.parsers.simulation_4d_engine import Simulation4DEngine

class TestSimulation4D(unittest.TestCase):
    def setUp(self):
        # Establish mock IFC-to-P6 mappings
        self.elements = [
            {"guid": "IFC-001", "start_date": "2026-08-01T00:00:00", "finish_date": "2026-08-10T00:00:00"},
            {"guid": "IFC-002", "start_date": "2026-08-11T00:00:00", "finish_date": "2026-08-20T00:00:00", "is_critical": True, "delay_days": 5},
            {"guid": "IFC-003", "start_date": "2026-08-21T00:00:00", "finish_date": "2026-08-30T00:00:00"}
        ]

    def test_chronological_planned_state(self):
        # Simulate time well before construction starts
        snap = Simulation4DEngine.generate_timeline_snapshots(self.elements, "2026-07-25T00:00:00")
        self.assertEqual(snap["element_states"]["IFC-001"]["state"], "PLANNED")
        self.assertEqual(snap["element_states"]["IFC-001"]["progress"], 0)

    def test_chronological_in_progress_state(self):
        # Simulate time exactly in the middle of IFC-001
        snap = Simulation4DEngine.generate_timeline_snapshots(self.elements, "2026-08-05T12:00:00")
        self.assertEqual(snap["element_states"]["IFC-001"]["state"], "IN_PROGRESS")
        self.assertGreater(snap["element_states"]["IFC-001"]["progress"], 0)
        self.assertLess(snap["element_states"]["IFC-001"]["progress"], 100)

    def test_chronological_completed_state(self):
        # Simulate time after IFC-001 finishes
        snap = Simulation4DEngine.generate_timeline_snapshots(self.elements, "2026-08-15T00:00:00")
        self.assertEqual(snap["element_states"]["IFC-001"]["state"], "COMPLETED")
        self.assertEqual(snap["element_states"]["IFC-001"]["progress"], 100)

    def test_critical_delay_detection_state(self):
        # Simulate time during IFC-002, which is flagged as delayed and critical
        snap = Simulation4DEngine.generate_timeline_snapshots(self.elements, "2026-08-15T00:00:00")
        self.assertEqual(snap["element_states"]["IFC-002"]["state"], "CRITICAL_DELAY")

if __name__ == "__main__":
    unittest.main()
