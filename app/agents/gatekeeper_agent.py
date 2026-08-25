"""
Gatekeeper Agent Node.

Runs the PreSubmissionAuditor across the full tender state, computes the
bid-readiness score, and issues a cryptographic clearance certificate when all
checks pass. Mutates ``qa_readiness_score`` and ``final_qa_dossier`` on state.
"""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.parsers.pre_submission_auditor import PreSubmissionAuditor
from app.schemas.gatekeeper import PreSubmissionReport, SubmissionClearanceCertificate


def _clearance_checksum(report: PreSubmissionReport, project_id: int | None) -> str:
    """SHA-256 checksum over the fully-passed report payload (tamper-evident)."""
    payload = {
        "project_id": project_id,
        "bid_readiness_score": report.bid_readiness_score,
        "passed_checks": report.passed_checks,
        "total_checks": report.total_checks,
        "is_cleared": report.is_cleared_for_submission,
        "categories": [c.category for c in report.categories],
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def gatekeeper_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: pre-submission QA gatekeeper.

    State keys consumed: boq_items, sbc_compliance_matrix, ve_matrix,
      attachments, financial_summary, cost_breakdown_structure,
      proposal_artifacts, contract_value_sar, bid_validity_days, warranty_months.
    State keys produced: qa_readiness_score, final_qa_dossier,
      submission_clearance (when cleared).
    """
    print("--- [AGENT] Pre-Submission Gatekeeper ---")

    project_id = state.get("project_id") or state.get("tender_id")
    report = PreSubmissionAuditor.run_full_audit(state, project_id=project_id)

    dossier: Dict[str, Any] = {
        "bid_readiness_score": report.bid_readiness_score,
        "is_cleared_for_submission": report.is_cleared_for_submission,
        "total_checks": report.total_checks,
        "passed_checks": report.passed_checks,
        "failed_checks": report.failed_checks,
        "categories": [cat.model_dump() for cat in report.categories],
        "blocking_issues": report.blocking_issues,
    }

    mutation: Dict[str, Any] = {
        "qa_readiness_score": report.bid_readiness_score,
        "final_qa_dossier": dossier,
    }

    if report.is_cleared_for_submission:
        checksum = _clearance_checksum(report, project_id)
        valid_until = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        certificate = SubmissionClearanceCertificate(
            project_id=project_id,
            clearance_checksum=checksum,
            bid_readiness_score=report.bid_readiness_score,
            authorized_at=datetime.now(timezone.utc).isoformat(),
            valid_until=valid_until,
            signed_payload={
                "passed_checks": report.passed_checks,
                "total_checks": report.total_checks,
                "categories": [c.category for c in report.categories],
            },
        )
        mutation["submission_clearance"] = certificate.model_dump()
        print(f"[GATEKEEPER] CLEARED — checksum {checksum[:16]}…")
    else:
        mutation["submission_clearance"] = None
        print(
            f"[GATEKEEPER] BLOCKED — {len(report.blocking_issues)} blocking issues: "
            f"{report.blocking_issues[:3]}"
        )

    return mutation
