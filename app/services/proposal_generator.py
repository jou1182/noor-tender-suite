from typing import List, Dict, Any

class ProposalGeneratorService:
    @staticmethod
    def generate_method_statement(boq_item: str, specs: str) -> Dict[str, Any]:
        """
        Simulates an LLM chain that generates domain-specific method statements.
        It parses BOQ descriptors to retrieve structural domain prompts.
        """
        boq_lower = boq_item.lower()
        
        if "concrete" in boq_lower:
            statement = "1. Surface preparation.\n2. Formwork installation.\n3. Steel reinforcement placement in compliance with rebar spacing rules.\n4. Pouring and vibration.\n5. Curing for 7 days. Compliant with SBC 304 guidelines for severe exposure."
            crew = ["1 Foreman", "4 Carpenters", "4 Steel Fixers", "6 Laborers"]
            equipment = ["Concrete Pump", "Vibrators", "Tower Crane"]
            productivity = 40.0 # m3/day
        elif "excavat" in boq_lower or "earthwork" in boq_lower:
            statement = "1. Site surveying and marking.\n2. Utility clearance.\n3. Mechanical excavation to required depth.\n4. Shoring installation if depth > 1.5m. Compliant with SBC 303 geotechnical regulations."
            crew = ["1 Supervisor", "2 Operators", "3 Laborers", "1 Surveyor"]
            equipment = ["Excavator (20t)", "Dump Trucks (20m3)", "Compactor"]
            productivity = 150.0 # m3/day
        else:
            statement = f"Standard technical methodology for {boq_item} based on general engineering practices and provided specifications."
            crew = ["1 Foreman", "2 Skilled Workers", "2 Laborers"]
            equipment = ["Standard Toolset"]
            productivity = 20.0
            
        return {
            "boq_item": boq_item,
            "method_statement_text": statement,
            "crew_composition": crew,
            "equipment_allocation": equipment,
            "productivity_rate": productivity,
            "unit": "units/day"
        }

    @staticmethod
    def build_full_proposal(boq_items: List[str], rfp_specs: str) -> List[Dict[str, Any]]:
        return [ProposalGeneratorService.generate_method_statement(item, rfp_specs) for item in boq_items]
