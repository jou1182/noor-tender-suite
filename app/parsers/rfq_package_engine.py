import re
from typing import Dict, List, Any

class RfqPackageEngine:
    # CSI Standard Keyword Domain Mapper
    TRADE_MAP = {
        "Earthworks (CSI 31)": [r"excavat", r"backfill", r"soil", r"trench", r"grading", r"earth"],
        "Concrete (CSI 03)": [r"concrete", r"rebar", r"formwork", r"cement", r"slab", r"foundation"],
        "Piping & Utilities (CSI 33)": [r"pipe", r"valve", r"fitting", r"duct", r"manhole", r"drain"],
        "MEP (CSI 21-28)": [r"cable", r"wire", r"pump", r"motor", r"hvac", r"light", r"electrical"]
    }

    @staticmethod
    def cluster_boq_items(boq_lines: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Dynamically clusters flat BOQ line items into specialized structural trade packages.
        """
        packages = {trade: [] for trade in RfqPackageEngine.TRADE_MAP.keys()}
        packages["General Requirements"] = []
        
        for line in boq_lines:
            desc = line.get("description", "").lower()
            matched = False
            for trade, keywords in RfqPackageEngine.TRADE_MAP.items():
                if any(re.search(kw, desc) for kw in keywords):
                    packages[trade].append(line)
                    matched = True
                    break
            
            # Fallback for unclassified indirect items
            if not matched:
                packages["General Requirements"].append(line)
                
        # Strip empty packages to optimize token payload
        return {k: v for k, v in packages.items() if v}

    @staticmethod
    def normalize_vendor_bids(package_budget: float, vendor_quotes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes competing subcontractor bids by structurally penalizing missing scope variables.
        Applies a defensive 10% premium on unquoted fractions to protect the overall tender budget.
        """
        evaluations = []
        for vendor in vendor_quotes:
            raw_bid = vendor.get("bid_amount", 0.0)
            scope_coverage = vendor.get("scope_coverage_pct", 100.0)
            
            # Normalization Formula: Add standard pricing + 10% penalty for any omitted scope
            missing_scope_pct = max(0, 100.0 - scope_coverage) / 100.0
            missing_budget_val = missing_scope_pct * package_budget
            normalized_penalty = missing_budget_val * 1.10
            
            normalized_bid = raw_bid + normalized_penalty
            variance_to_budget = normalized_bid - package_budget
            
            evaluations.append({
                "vendor_name": vendor["vendor_name"],
                "raw_bid": raw_bid,
                "scope_coverage_pct": scope_coverage,
                "normalized_penalty": normalized_penalty,
                "normalized_bid": normalized_bid,
                "variance_to_budget": variance_to_budget,
                "is_optimal": False # Resolved during ranking
            })
            
        # Algorithmic sorting for Optimal Vendor Target Selection
        evaluations.sort(key=lambda x: x["normalized_bid"])
        if evaluations:
            evaluations[0]["is_optimal"] = True
            
        return evaluations
