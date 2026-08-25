import math
from typing import Dict, Any, List

class EngineeringMathEngine:
    @staticmethod
    def check_manning_capacity(diameter_m: float, slope: float, n_roughness: float, required_flow_m3s: float) -> Dict[str, Any]:
        radius = diameter_m / 2.0
        area = math.pi * (radius ** 2)
        wetted_perimeter = 2 * math.pi * radius
        hydraulic_radius = area / wetted_perimeter if wetted_perimeter > 0 else 0
        
        # Q = (1/n) * A * R^(2/3) * S^(1/2)
        capacity = (1.0 / n_roughness) * area * (hydraulic_radius ** (2.0/3.0)) * math.sqrt(slope)
        
        is_safe = capacity >= required_flow_m3s
        
        return {
            "check_name": "Hydraulic Pipe Capacity (Manning)",
            "calculated_value": round(capacity, 4),
            "required_value": required_flow_m3s,
            "unit": "m³/s",
            "is_safe": is_safe,
            "warning": f"Pipe undersized! Capacity {round(capacity, 4)} m³/s < Required {required_flow_m3s} m³/s" if not is_safe else "Capacity sufficient."
        }

    @staticmethod
    def check_soil_bearing(applied_stress_kpa: float, ultimate_bearing_capacity_kpa: float) -> Dict[str, Any]:
        fos = ultimate_bearing_capacity_kpa / applied_stress_kpa if applied_stress_kpa > 0 else float('inf')
        min_fos = 3.0 # Standard SBC 303 minimum FOS for shallow foundations
        
        is_safe = fos >= min_fos
        return {
            "check_name": "Soil Bearing Capacity (SBC 303)",
            "calculated_value": round(fos, 2),
            "required_value": min_fos,
            "unit": "FOS",
            "is_safe": is_safe,
            "warning": f"Factor of Safety too low! {round(fos, 2)} < {min_fos}" if not is_safe else "FOS sufficient."
        }

    @staticmethod
    def check_concrete_durability(cement_content_kg: float, wc_ratio: float) -> List[Dict[str, Any]]:
        # SBC 304 defaults for severe exposure
        min_cement = 350.0 
        max_wc = 0.45
        
        results = []
        
        # Cement Check
        is_cement_safe = cement_content_kg >= min_cement
        results.append({
            "check_name": "Min Cement Content (SBC 304)",
            "calculated_value": cement_content_kg,
            "required_value": min_cement,
            "unit": "kg/m³",
            "is_safe": is_cement_safe,
            "warning": f"Cement content inadequate! {cement_content_kg} < {min_cement} kg/m³" if not is_cement_safe else "Cement content acceptable."
        })
        
        # W/C Ratio Check
        is_wc_safe = wc_ratio <= max_wc
        results.append({
            "check_name": "Max W/C Ratio (SBC 304)",
            "calculated_value": wc_ratio,
            "required_value": max_wc,
            "unit": "Ratio",
            "is_safe": is_wc_safe,
            "warning": f"W/C ratio too high! {wc_ratio} > {max_wc}" if not is_wc_safe else "W/C ratio acceptable."
        })
        
        return results
