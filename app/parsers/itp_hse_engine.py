import re
from typing import Dict, List, Any

class ItpHseEngine:
    @staticmethod
    def generate_itp(boq_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Dynamically analyzes BOQ descriptions to mandate strict Inspection & Test Plan (ITP) activities.
        Assigns governing ISO/ASTM/SBC standards and dictates control checkpoints (Hold/Witness/Review).
        """
        itp_register = []
        
        for line in boq_lines:
            desc = line.get("description", "").lower()
            
            if "concrete" in desc or "rebar" in desc:
                itp_register.extend([
                    {"activity": "Structural Rebar Inspection", "reference": "SBC 304", "frequency": "Before every pour", "checkpoint": "Hold Point"},
                    {"activity": "Fresh Concrete Slump & Temp", "reference": "ASTM C143", "frequency": "Every transit mixer", "checkpoint": "Witness Point"},
                    {"activity": "Compressive Strength Testing", "reference": "ASTM C39", "frequency": "7 & 28 Days", "checkpoint": "Hold Point"}
                ])
                
            if "excavat" in desc or "trench" in desc or "backfill" in desc:
                itp_register.extend([
                    {"activity": "Formation Compaction Test (FDT)", "reference": "ASTM D1556", "frequency": "Every layer (250mm)", "checkpoint": "Witness Point"},
                    {"activity": "Geotech Soil Bearing Review", "reference": "SBC 303", "frequency": "Bottom of excavation", "checkpoint": "Hold Point"}
                ])
                
        # Deduplicate activities to construct a clean Master ITP
        unique_itp = {item["activity"]: item for item in itp_register}.values()
        return list(unique_itp)

    @staticmethod
    def compute_hira(boq_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Computes the Hazard Identification and Risk Assessment (HIRA) Matrix.
        Evaluates operational severity and probability to output risk scores and strict mitigations.
        """
        hira_register = []
        
        for line in boq_lines:
            desc = line.get("description", "").lower()
            
            if "trench" in desc or "excavat" in desc:
                # Probability(4) * Severity(4) = 16 (HIGH RISK)
                hira_register.append({
                    "task": "Deep Trench / Mass Excavation",
                    "hazard": "Cave-in / Collapse / Asphyxiation",
                    "probability": 4,
                    "severity": 4,
                    "risk_score": 16,
                    "mitigation": "Install engineered shoring system. Daily atmospheric testing. Confined space permit required."
                })
                
            if "concrete" in desc:
                # Probability(3) * Severity(3) = 9 (MODERATE RISK)
                hira_register.append({
                    "task": "High-Volume Concrete Pouring",
                    "hazard": "Pump line failure / Chemical burns",
                    "probability": 3,
                    "severity": 3,
                    "risk_score": 9,
                    "mitigation": "Mandatory PPE (alkali-resistant). Daily ultrasonic thickness checks on pump elbows."
                })
                
        # Deduplicate to construct Master HSE Risk Register
        unique_hira = {item["task"]: item for item in hira_register}.values()
        return list(unique_hira)
