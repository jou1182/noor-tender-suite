import re

class DataSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        """
        Masks highly sensitive commercial telemetry and financial indicators
        before transmitting to upstream external LLM APIs (OpenAI, Anthropic, etc).
        """
        # 1. Mask Financial Monetary Amounts (e.g., SAR 50,000,000.00)
        text = re.sub(r'SAR\s*[\d,]+(?:\.\d+)?', 'SAR [AMOUNT_REDACTED]', text, flags=re.IGNORECASE)
        
        # 2. Mask Bank Guarantees / LC references
        text = re.sub(r'(?:BG|Guarantee|LC)\s*(?:No\.?)?\s*[\d-]+', '[BANK_GUARANTEE_REDACTED]', text, flags=re.IGNORECASE)
        
        # 3. Mask Commercial PII and Specific State-Owned Enterprises or Client Entities
        text = re.sub(r'(?i)\b(?:Alrawaf|Aramco|Saudi Aramco|SABIC|NEOM|Qiddiya|Red Sea Global)\b', '[COMPANY_NAME_REDACTED]', text)
        
        return text
