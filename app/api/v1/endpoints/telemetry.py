from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
from datetime import datetime
from typing import Any, Dict, List

from app.core.swarm_telemetry import drain
from app.core.sse_dispatcher import event_source, encode_sse

router = APIRouter()

# Latest computed RFP compliance matrix (published by the cross-exam agent).
# Served as an initial event so dashboards hydrate immediately on connect.
_latest_compliance: Dict[str, Any] | None = None


def set_latest_compliance(payload: Dict[str, Any]) -> None:
    """Store the most recent compliance matrix for late subscribers."""
    global _latest_compliance
    _latest_compliance = payload


async def mock_telemetry_generator():
    # Drain real-time agent telemetry published during live audits first.
    buffered = drain()
    for line in buffered:
        yield f"data: {line}\n\n"

    events = [
        "System Initializing...",
        "RFP Deconstructor Agent running — parsing RFP clauses and extracting requirements...",
        "Client BOQ Agent running — extracting bill of quantities...",
        "Methodology Auditor running — comparing method statements against SBC standards...",
        "P6 Schedule Auditor running — loading XER schedule file for DCMA analysis...",
        "Standards Agent running — querying Qdrant vector store for SBC requirements...",
        "QA/QC Agent running — building Inspection & Test Plan register...",
        "HSE Agent running — computing HIRA risk matrix...",
        "Cross-Exam Agent running — adversarial validation of extracted clauses...",
        "Red Team Agent running — probing tender package for vulnerabilities...",
        "Arbitrator Agent running — synthesizing final technical score...",
        "RFP Deconstructor Agent completed — clauses extracted and de-duplicated.",
        "Client BOQ Agent completed — line items parsed into structured matrix.",
        "Methodology Auditor completed — SBC compliance gaps flagged.",
        "P6 Schedule Auditor completed — DCMA 14-point integrity check executed.",
        "Standards Agent completed — SBC requirements mapped to clause matrix.",
        "QA/QC Agent completed — Inspection & Test Plan register published.",
        "HSE Agent completed — HIRA risk register computed.",
        "Cross-Exam Agent completed — discrepancies surfaced for arbitration.",
        "Red Team Agent completed — high-risk findings confirmed.",
        "Final synthesis scoring complete. Finalizing compliance matrix..."
    ]
    for event in events:
        await asyncio.sleep(0.7)
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        yield f"data: [{timestamp}] [AGENT_TELEMETRY] {event}\n\n"

    yield "data: [END] Stream completed.\n\n"


@router.get("/stream")
async def stream_telemetry():
    """
    Endpoint providing live SSE telemetry for the frontend dashboard to render live logs.
    Public demo stream (mock data) so the browser EventSource can consume it without auth.
    """
    return StreamingResponse(mock_telemetry_generator(), media_type="text/event-stream")


@router.get("/stream/compliance")
async def stream_rfp_compliance():
    """
    SSE stream for structured ``rfp_compliance_update`` events emitted by the
    Cross-Exam Agent during a live audit. Each event carries:
      - overall compliance score
      - classified clauses (COMPLIANT / MINOR_DEVIATION / CRITICAL_GAP)
      - gap summaries
      - AI-generated remediation narratives

    Emits the most recently computed matrix first so the studio hydrates
    immediately even if the audit completed before the client connected.
    """
    initial: List[Dict[str, Any]] = []
    if _latest_compliance is not None:
        initial.append(_latest_compliance)

    return StreamingResponse(
        event_source("rfp_compliance_update", initial),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# In-memory LLM gateway telemetry accumulator (published by the LLM router).
_llm_telemetry: Dict[str, Any] = {
    "total_tokens": 0,
    "total_cost_usd": 0.0,
    "active_model": "gpt-4-turbo",
    "models_distribution": {"gpt-4-turbo": 0, "claude-3-opus": 0, "gemini-1.5-pro": 0},
}


def record_llm_usage(model: str, tokens: int, cost_usd: float) -> None:
    """Accumulate LLM usage telemetry for the live stream."""
    _llm_telemetry["total_tokens"] += int(tokens)
    _llm_telemetry["total_cost_usd"] = round(_llm_telemetry["total_cost_usd"] + float(cost_usd), 6)
    _llm_telemetry["active_model"] = model
    _llm_telemetry["models_distribution"][model] = _llm_telemetry["models_distribution"].get(model, 0) + int(tokens)


@router.get("/llm-stream")
async def stream_llm_telemetry():
    """
    SSE stream of real-time LLM gateway telemetry: token counts, cost accruals,
    active model, and swarm model-distribution percentages.
    """

    async def generator():
        # Emit the current snapshot first, then a heartbeat + drift demo.
        yield encode_sse("llm_snapshot", dict(_llm_telemetry))
        while True:
            await asyncio.sleep(2.0)
            # Simulated live drift for the demo (production binds the real router).
            record_llm_usage("gpt-4-turbo", 120, 0.0018)
            yield encode_sse("llm_update", dict(_llm_telemetry))
            yield ": keep-alive\n\n"

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
