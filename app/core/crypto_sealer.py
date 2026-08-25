import json
import hashlib
from datetime import datetime
from typing import Dict, Any

class CryptoSealer:
    @staticmethod
    def hash_payload(payload: Any) -> str:
        """
        Generates a deterministic SHA-256 cryptographic hash for a given data payload.
        Ensures consistent ordering for JSON dictionary representations.
        """
        payload_str = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_payload(payload: Any, expected_hash: str) -> bool:
        """
        Verifies payload integrity against an expected cryptographic hash.
        Used to detect tampering post-generation.
        """
        return CryptoSealer.hash_payload(payload) == expected_hash

    @staticmethod
    def generate_manifest(sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a cryptographic manifest containing individual section hashes 
        and an overarching master dossier signature for strict legal auditability.
        """
        manifest = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "signatures": {}
        }
        
        # Calculate isolated hashes for every module of the technical proposal
        for section_name, content in sections.items():
            if content:
                manifest["signatures"][section_name] = CryptoSealer.hash_payload(content)
            else:
                manifest["signatures"][section_name] = "MISSING"
                
        # Generate the ultimate Master Hash bridging the entire submission structure
        manifest["master_hash"] = CryptoSealer.hash_payload(manifest["signatures"])
        
        return manifest
