from typing import Any, Dict
from app.parsers.gis_engine import GISEngine

def geotech_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Extract mock project alignment coordinates
    project_coords = state.get("project_coordinates", [
        (24.7136, 46.6753),
        (24.7200, 46.6800)
    ])
    
    # Pre-loaded regional hazard zones (e.g., Karstic Limestone, High Groundwater)
    hazard_zones = [
        {
            "name": "High Groundwater Zone (Requires Dewatering)",
            "polygon": [
                (24.7150, 46.6700),
                (24.7250, 46.6700),
                (24.7250, 46.6900),
                (24.7150, 46.6900)
            ]
        }
    ]
    
    gis_results = GISEngine.evaluate_site_context(project_coords, hazard_zones)
    
    # Cross-examine against Contractor's Proposed Methodology (e.g., missing Dewatering)
    methodology = state.get("methodology_output", {})
    proposed_methods = methodology.get("methods", [])
    
    alerts = []
    if "High Groundwater Zone (Requires Dewatering)" in gis_results["hazard_zones"]:
        if "Dewatering" not in proposed_methods:
            alerts.append("CRITICAL SPATIAL MISMATCH: Project alignment intersects a known High Groundwater Zone, but 'Dewatering' operations are missing from the proposed Method Statement.")
            
    gis_results["geotech_alerts"] = alerts
    
    return {"geotech_output": gis_results}
