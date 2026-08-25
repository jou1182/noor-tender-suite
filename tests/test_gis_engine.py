import unittest
from app.parsers.gis_engine import GISEngine

class TestGISEngine(unittest.TestCase):
    def test_calculate_length(self):
        coords = [(0.0, 0.0), (0.0, 1.0)] # 1 degree diff in y
        length = GISEngine.calculate_alignment_length(coords)
        self.assertAlmostEqual(length, 111000.0, places=1)
        
    def test_hazard_intersection(self):
        coords = [(0.0, 0.0), (2.0, 2.0)]
        hazard_zone = [(1.0, 0.0), (3.0, 0.0), (3.0, 3.0), (1.0, 3.0)] # Box from 1,0 to 3,3
        self.assertTrue(GISEngine.check_hazard_intersection(coords, hazard_zone))
        
        safe_coords = [(-1.0, -1.0), (0.5, 0.5)]
        self.assertFalse(GISEngine.check_hazard_intersection(safe_coords, hazard_zone))

    def test_evaluate_site_context(self):
        coords = [(24.7136, 46.6753), (24.7200, 46.6800)]
        hazard_zones = [{
            "name": "High Groundwater",
            "polygon": [(24.7150, 46.6700), (24.7250, 46.6700), (24.7250, 46.6900), (24.7150, 46.6900)]
        }]
        result = GISEngine.evaluate_site_context(coords, hazard_zones)
        self.assertTrue(result["intersects_hazards"])
        self.assertIn("High Groundwater", result["hazard_zones"])
        
if __name__ == "__main__":
    unittest.main()
