from typing import Dict, Any, List
import datetime

class FieldGatewayService:
    # Master lookup table mapping visual/audio defects to active building codes
    SBC_CODE_MAP = {
        "honeycombing": {"code": "SBC-304", "desc": "Concrete Structural Integrity Failure"},
        "cracks": {"code": "SBC-304", "desc": "Concrete Crack Tolerance Limit Exceeded"},
        "missing_shoring": {"code": "OSHA-1926", "desc": "Excavation Support & Trench Safety Failure"},
        "missing_ppe": {"code": "SBC-HSE", "desc": "Site Safety & Health Mandatory Equipment Regulations"}
    }

    @staticmethod
    def process_multimodal_field_report(voice_transcript: str, image_tags: List[str]) -> Dict[str, Any]:
        """
        Ingests unstructured field audio transcripts and AI-classified defect image tags.
        Cross-references defects against SBC building codes to automatically draft 
        structured Non-Conformance Reports (NCRs).
        """
        detected_defects = []
        
        # 1. NLP Analysis on Voice Transcript
        t_lower = voice_transcript.lower()
        if "crack" in t_lower:
            detected_defects.append("cracks")
        if "honeycomb" in t_lower:
            detected_defects.append("honeycombing")
        if "shoring" in t_lower or "collapse" in t_lower:
            detected_defects.append("missing_shoring")
            
        # 2. Vision Mapping from Image Classifications
        for tag in image_tags:
            if tag in FieldGatewayService.SBC_CODE_MAP and tag not in detected_defects:
                detected_defects.append(tag)
                
        # 3. NCR Generation Engine
        ncrs = []
        for defect in detected_defects:
            sbc_rule = FieldGatewayService.SBC_CODE_MAP[defect]
            
            ncrs.append({
                "ncr_id": f"NCR-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{defect.upper()[:4]}",
                "defect_type": defect.replace("_", " ").title(),
                "sbc_violation_code": sbc_rule["code"],
                "violation_desc": sbc_rule["desc"],
                "severity": "CRITICAL" if defect in ["honeycombing", "missing_shoring"] else "MODERATE",
                "status": "OPEN",
                "required_action": f"Immediate site remediation and Engineer review mandated per {sbc_rule['code']} guidelines."
            })
            
        return {
            "transcript_processed": voice_transcript,
            "vision_tags_processed": image_tags,
            "ncrs_issued": ncrs,
            "total_defects": len(ncrs),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
