import difflib
from typing import Dict, Any, List

class DriftEngine:
    @staticmethod
    def compare_versions(base_text: str, addendum_text: str, base_boq: Dict[str, float], addendum_boq: Dict[str, float]) -> Dict[str, Any]:
        # Text Diffs
        d = difflib.ndiff(base_text.splitlines(), addendum_text.splitlines())
        text_changes = []
        impacted_clauses = set()
        
        for line in d:
            if line.startswith('- '):
                text_changes.append({"type": "deletion", "content": line[2:]})
                if "Clause" in line:
                    parts = line.split()
                    if len(parts) > 2:
                        impacted_clauses.add(parts[2])
            elif line.startswith('+ '):
                text_changes.append({"type": "addition", "content": line[2:]})
                if "Clause" in line:
                    parts = line.split()
                    if len(parts) > 2:
                        impacted_clauses.add(parts[2])

        # BOQ Variances
        boq_variances = []
        all_items = set(base_boq.keys()).union(addendum_boq.keys())
        for item in all_items:
            base_qty = base_boq.get(item, 0.0)
            new_qty = addendum_boq.get(item, 0.0)
            if base_qty != new_qty:
                boq_variances.append({
                    "item": item,
                    "base_qty": base_qty,
                    "new_qty": new_qty,
                    "delta": new_qty - base_qty
                })
                
        return {
            "text_changes": text_changes,
            "impacted_clauses": list(impacted_clauses),
            "boq_variances": boq_variances
        }
