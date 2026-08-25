from shapely.geometry import LineString, Polygon
from typing import List, Tuple, Dict, Any

class GISEngine:
    @staticmethod
    def calculate_alignment_length(coordinates: List[Tuple[float, float]]) -> float:
        """Calculates approximate length of a line string given WGS84 coordinates."""
        if len(coordinates) < 2:
            return 0.0
        line = LineString(coordinates)
        # Simplified equirectangular approximation (1 deg ~ 111km) for fast local engine checks
        return line.length * 111000.0

    @staticmethod
    def check_hazard_intersection(project_coords: List[Tuple[float, float]], hazard_polygon: List[Tuple[float, float]]) -> bool:
        if len(project_coords) < 2 or len(hazard_polygon) < 3:
            return False
        project_line = LineString(project_coords)
        hazard_zone = Polygon(hazard_polygon)
        return project_line.intersects(hazard_zone)
        
    @staticmethod
    def evaluate_site_context(coords: List[Tuple[float, float]], hazard_zones: List[Dict[str, Any]]) -> Dict[str, Any]:
        length_m = GISEngine.calculate_alignment_length(coords)
        
        intersected_hazards = []
        for zone in hazard_zones:
            if GISEngine.check_hazard_intersection(coords, zone["polygon"]):
                intersected_hazards.append(zone["name"])
                
        return {
            "total_length_m": round(length_m, 2),
            "intersects_hazards": len(intersected_hazards) > 0,
            "hazard_zones": intersected_hazards,
            "risk_level": "HIGH" if intersected_hazards else "LOW"
        }
