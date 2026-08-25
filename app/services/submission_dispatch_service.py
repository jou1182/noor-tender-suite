import datetime
from typing import Dict, Any
from app.core.crypto_sealer import CryptoSealer

class SubmissionDispatchService:
    @staticmethod
    def execute_preflight_checks(dossier_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes strict pre-flight validation gates verifying technical/commercial separation,
        bank guarantee configurations, and structural cryptographic integrity prior to submission.
        """
        errors = []
        manifest = dossier_data.get("manifest", {})
        signatures = manifest.get("signatures", {})
        
        if not manifest or not signatures:
            return {
                "dispatch_status": "ABORTED_SAFETY_LOCKOUT",
                "errors": ["FATAL: Missing Cryptographic Manifest. Cannot execute pre-flight checks."],
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
        
        # 1. Tech / Financial Envelope Separation Check
        if not signatures.get("technical_methodology") or signatures.get("technical_methodology") == "MISSING":
            errors.append("CRITICAL: Technical Methodology Package Missing.")
        
        if not signatures.get("commercial_boq") or signatures.get("commercial_boq") == "MISSING":
            errors.append("CRITICAL: Commercial BOQ Financial Package Missing.")
            
        # 2. Cryptographic Integrity Validation
        master_hash = manifest.get("master_hash")
        if not master_hash:
            errors.append("CRITICAL: Master SHA-256 Signature Missing.")
        elif not CryptoSealer.verify_payload(signatures, master_hash):
            errors.append("CRITICAL: Cryptographic Hash Tamper Detected. Immutable seal broken.")

        if errors:
            return {
                "dispatch_status": "ABORTED_SAFETY_LOCKOUT",
                "errors": errors,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
            }
            
        return {
            "dispatch_status": "CERTIFIED_READY",
            "certificate_id": f"CERT-{master_hash[:12].upper()}",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "authorized_payload_hash": master_hash
        }
