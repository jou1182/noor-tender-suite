from typing import Dict, Any
from app.services.field_gateway_service import FieldGatewayService

def field_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multimodal Field Operations Agent Node.
    Extracts real-time site feeds (Voice/Vision) and executes the Field Gateway Service 
    to output structured Non-Conformance Reports (NCR) into the Orchestration State.
    """
    print("--- [AGENT] Field Operations Site Inspector ---")
    
    # Simulate extraction of raw multimodal telemetry feeds ingested from mobile site engineers
    field_raw = state.get("field_raw_input", {
        "voice_memo": "Observer detected significant honeycombing on column C4 at level 2 drop panel. Also noticed missing PPE on the rebar team.",
        "image_tags": ["honeycombing", "missing_ppe"]
    })
    
    field_output = FieldGatewayService.process_multimodal_field_report(
        voice_transcript=field_raw.get("voice_memo", ""),
        image_tags=field_raw.get("image_tags", [])
    )
    
    return {"field_output": field_output}
