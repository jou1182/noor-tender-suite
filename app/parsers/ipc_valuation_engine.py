from typing import Dict, Any

class IpcValuationEngine:
    @staticmethod
    def calculate_ipc(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates Interim Payment Certificates (IPC) securely.
        Enforces 10% Retention limits against a 5% cap, strictly monitors advance payment 
        amortizations, and automatically injects 15% standard VAT.
        """
        contract_value = data.get("contract_value", 0.0)
        previous_gross = data.get("previous_gross", 0.0)
        previous_net = data.get("previous_net", 0.0)
        current_work_done = data.get("current_work_done", 0.0)
        materials_on_site = data.get("materials_on_site", 0.0)
        
        # Advance Payment Details
        advance_total = data.get("advance_payment_total", 0.0)
        advance_recovered_previously = data.get("advance_recovered_previously", 0.0)
        advance_recovery_rate = data.get("advance_recovery_rate", 0.10) # 10% Recovery standard
        
        # Retention Holdback Details
        retention_rate = data.get("retention_rate", 0.10) # 10% standard Holdback
        retention_cap_rate = data.get("retention_cap_rate", 0.05) # Capped at 5% of Total Contract
        
        # Penalties
        liquidated_damages = data.get("liquidated_damages", 0.0)
        
        # 1. Cumulative Gross Valuation
        cumulative_gross = previous_gross + current_work_done + materials_on_site
        
        # 2. Retention Calculation (Enforce Cap)
        calculated_retention = cumulative_gross * retention_rate
        max_retention = contract_value * retention_cap_rate
        actual_retention = min(calculated_retention, max_retention)
        
        # 3. Advance Payment Amortization (Enforce Zero-Balance limit)
        calculated_recovery = current_work_done * advance_recovery_rate
        remaining_advance = advance_total - advance_recovered_previously
        actual_recovery = min(calculated_recovery, remaining_advance)
        
        # 4. Total Deductions Accumulation
        total_deductions = actual_retention + actual_recovery + advance_recovered_previously + liquidated_damages
        
        # 5. Cumulative Net Valuation
        cumulative_net = cumulative_gross - total_deductions
        
        # 6. Amount Due This IPC (Pre-VAT)
        amount_due = max(0.0, cumulative_net - previous_net)
        
        # 7. VAT calculation (15%)
        vat_amount = amount_due * 0.15
        
        # 8. Final Certified Payment
        total_certified = amount_due + vat_amount
        
        return {
            "contract_value": contract_value,
            "cumulative_gross": cumulative_gross,
            "actual_retention": actual_retention,
            "actual_recovery": actual_recovery,
            "liquidated_damages": liquidated_damages,
            "total_deductions": total_deductions,
            "cumulative_net": cumulative_net,
            "amount_due_pre_vat": amount_due,
            "vat_amount": vat_amount,
            "total_certified_payment": total_certified,
            "advance_payment_balance": remaining_advance - actual_recovery,
            "retention_balance_to_cap": max(0.0, max_retention - actual_retention)
        }
