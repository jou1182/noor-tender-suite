from typing import Any, Dict
from app.parsers.engineering_math_engine import EngineeringMathEngine

def calculation_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    # Mock parameter extraction from LLM/NLP processing of technical method statements
    extracted_params = state.get("technical_parameters", {
        "pipe_diameter_m": 0.5,
        "pipe_slope": 0.01,
        "n_roughness": 0.013,
        "required_flow": 1.2, # Highly likely to fail Manning check for a 0.5m pipe
        "applied_stress": 150.0,
        "ultimate_bearing": 500.0, # FOS = 3.33 (Safe)
        "cement_content": 320.0, # Will fail SBC 304 (requires 350 min)
        "wc_ratio": 0.50 # Will fail SBC 304 (requires 0.45 max)
    })
    
    checks = []
    
    # 1. Pipe Capacity Validation
    checks.append(EngineeringMathEngine.check_manning_capacity(
        extracted_params["pipe_diameter_m"],
        extracted_params["pipe_slope"],
        extracted_params["n_roughness"],
        extracted_params["required_flow"]
    ))
    
    # 2. Soil Bearing FOS Verification
    checks.append(EngineeringMathEngine.check_soil_bearing(
        extracted_params["applied_stress"],
        extracted_params["ultimate_bearing"]
    ))
    
    # 3. Concrete Mix Durability Evaluation
    checks.extend(EngineeringMathEngine.check_concrete_durability(
        extracted_params["cement_content"],
        extracted_params["wc_ratio"]
    ))
    
    return {"calculation_output": {"checks": checks}}
