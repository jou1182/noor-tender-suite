"""
Pre-Submission Auditor Engine.

Executes deterministic gatekeeper QA across five dimensions before bid
authorization:

  1. SBC_STRUCTURAL  — zero active SBC-304 violations allowed.
  2. ARITHMETIC      — reconcile BOQ totals, S-Curve expenditures, ERP CBS.
  3. ATTACHMENTS     — mandatory bid attachments present.
  4. CONTRACTUAL     — bid validity window + warranty vs RFP mandates.
  5. PROPOSAL        — all proposal chapters, tables, signature blocks present.

Outputs a ``PreSubmissionReport`` with a bid-readiness score and any
FATAL_FLAW-driven blocking issues.
"""

from typing import Any, Dict, List

from app.schemas.gatekeeper import PreSubmissionReport, QAAuditCategory, QACheckItem

FATAL = "FATAL_FLAW"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

MANDATORY_ATTACHMENTS = [
    "commercial_registration",
    "contractor_classification",
    "bank_guarantee_draft",
]

REQUIRED_CHAPTERS = [
    "Executive Summary",
    "Project Scope",
    "Value Engineering",
    "SBC-304 Compliance",
    "Method Statements",
    "Risk Register",
    "Technical Evaluation",
]


def _check(check_id: str, description: str, passed: bool, severity: str, detail: str = "") -> QACheckItem:
    return QACheckItem(check_id=check_id, description=description, passed=passed, severity=severity, detail=detail)


class PreSubmissionAuditor:
    """Deterministic pre-submission QA auditor."""

    @staticmethod
    def audit_sbc_structural(state: Dict[str, Any]) -> QAAuditCategory:
        """Zero active SBC-304 violations allowed."""
        checks: List[QACheckItem] = []
        violations: List[Dict[str, Any]] = []

        # Collect from multiple state surfaces (matrix rows, cross-exam, VE cards).
        matrix = state.get("sbc_compliance_matrix", {}) or state.get("rfp_compliance_matrix", {}) or {}
        rows = matrix.get("matrix") or matrix.get("cards") or []
        for row in rows:
            status = row.get("status", "")
            if status in ("NON_COMPLIANT", "CRITICAL_GAP", "BLOCKED"):
                violations.append({"ref": row.get("clause_ref") or row.get("boq_item"), "status": status})

        ve_cards = state.get("ve_matrix", []) or []
        for card in ve_cards:
            if isinstance(card, dict) and card.get("sbc_status") == "BLOCKED":
                violations.append({"ref": card.get("boq_item"), "status": "BLOCKED"})

        checks.append(
            _check(
                "SBC-1",
                "All SBC-304 structural flags resolved (zero active violations)",
                passed=len(violations) == 0,
                severity=FATAL if violations else LOW,
                detail=(
                    f"{len(violations)} active violations: "
                    + "; ".join(f"{v['ref']} ({v['status']})" for v in violations[:5])
                    if violations
                    else "All SBC-304 flags clear."
                ),
            )
        )
        return QAAuditCategory(
            category="SBC_STRUCTURAL",
            checks=checks,
            passed_count=sum(1 for c in checks if c.passed),
            failed_count=sum(1 for c in checks if not c.passed),
            fatal_count=sum(1 for c in checks if not c.passed and c.severity == FATAL),
            fully_passed=all(c.passed for c in checks),
        )

    @staticmethod
    def audit_arithmetic(state: Dict[str, Any]) -> QAAuditCategory:
        """Reconcile BOQ totals, S-Curve total expenditures, ERP CBS allocations."""
        checks: List[QACheckItem] = []

        # 1. BOQ item arithmetic: qty * unit_rate == total (within epsilon).
        boq_items = state.get("boq_items", []) or []
        boq_mismatches = 0
        for item in boq_items:
            qty = float(item.get("qty", 0) or 0)
            rate = float(item.get("unit_rate", item.get("unit_rate_sar", 0)) or 0)
            total = float(item.get("total_amount", item.get("total_amount_sar", 0)) or 0)
            if qty and rate and abs(qty * rate - total) > 1.0:
                boq_mismatches += 1
        checks.append(
            _check(
                "ARITH-1",
                "BOQ line arithmetic consistent (qty x rate = total)",
                passed=boq_mismatches == 0,
                severity=FATAL if boq_mismatches else LOW,
                detail=f"{boq_mismatches} line mismatches found." if boq_mismatches else "BOQ arithmetic verified.",
            )
        )

        # 2. S-Curve total vs contract value.
        scurve = state.get("financial_summary", {}) or state.get("s_curve", {}) or {}
        scurve_total = float(scurve.get("total_expenditure_sar", scurve.get("total_planned_sar", 0)) or 0)
        contract_value = float(state.get("contract_value_sar", 0) or 0)
        if contract_value and scurve_total:
            mismatch = abs(scurve_total - contract_value) / contract_value
            passed = mismatch <= 0.01
        else:
            passed = True
            mismatch = 0.0
        checks.append(
            _check(
                "ARITH-2",
                "S-Curve total expenditure reconciles to contract value",
                passed=passed,
                severity=HIGH if not passed else LOW,
                detail=(
                    f"S-Curve {scurve_total:,.2f} vs contract {contract_value:,.2f} "
                    f"(variance {mismatch * 100:.2f}%)"
                    if contract_value
                    else "S-Curve or contract value absent — skipped."
                ),
            )
        )

        # 3. ERP CBS allocations sum to BOQ totals.
        cbs = state.get("cost_breakdown_structure", {}) or {}
        cbs_items = cbs.get("cbs_items", []) if isinstance(cbs, dict) else []
        cbs_total = sum(float(i.get("total_amount_sar", 0) or 0) for i in cbs_items)
        boq_total = sum(float(i.get("total_amount", i.get("total_amount_sar", 0)) or 0) for i in boq_items)
        if boq_total and cbs_total:
            passed = abs(cbs_total - boq_total) / boq_total <= 0.01
        else:
            passed = True
        checks.append(
            _check(
                "ARITH-3",
                "ERP CBS allocations reconcile to BOQ totals",
                passed=passed,
                severity=HIGH if not passed else LOW,
                detail=(
                    f"CBS {cbs_total:,.2f} vs BOQ {boq_total:,.2f}"
                    if boq_total
                    else "CBS or BOQ totals absent — skipped."
                ),
            )
        )

        return QAAuditCategory(
            category="ARITHMETIC",
            checks=checks,
            passed_count=sum(1 for c in checks if c.passed),
            failed_count=sum(1 for c in checks if not c.passed),
            fatal_count=sum(1 for c in checks if not c.passed and c.severity == FATAL),
            fully_passed=all(c.passed for c in checks),
        )

    @staticmethod
    def audit_attachments(state: Dict[str, Any]) -> QAAuditCategory:
        """Mandatory bidding attachments present."""
        attachments = state.get("attachments", []) or []
        names = {str(a.get("name", a if isinstance(a, str) else "")).lower() for a in attachments}

        checks: List[QACheckItem] = []
        for required in MANDATORY_ATTACHMENTS:
            present = any(required in name for name in names)
            checks.append(
                _check(
                    f"ATT-{required.upper()}",
                    f"Mandatory attachment: {required.replace('_', ' ').title()}",
                    passed=present,
                    severity=FATAL if not present else LOW,
                    detail="Present." if present else f"Missing '{required}'.",
                )
            )
        return QAAuditCategory(
            category="ATTACHMENTS",
            checks=checks,
            passed_count=sum(1 for c in checks if c.passed),
            failed_count=sum(1 for c in checks if not c.passed),
            fatal_count=sum(1 for c in checks if not c.passed and c.severity == FATAL),
            fully_passed=all(c.passed for c in checks),
        )

    @staticmethod
    def audit_contractual(state: Dict[str, Any]) -> QAAuditCategory:
        """Bid validity window and warranty terms vs RFP mandates."""
        checks: List[QACheckItem] = []

        rfp_min_validity = float(state.get("rfp_min_validity_days", 90) or 90)
        bid_validity = float(state.get("bid_validity_days", 0) or 0)
        passed = bid_validity >= rfp_min_validity if bid_validity else False
        checks.append(
            _check(
                "CONT-1",
                f"Bid validity ({bid_validity:.0f}d) meets RFP minimum ({rfp_min_validity:.0f}d)",
                passed=passed,
                severity=FATAL if not passed else LOW,
                detail=f"Bid validity {bid_validity:.0f}d vs required {rfp_min_validity:.0f}d."
                if bid_validity
                else "Bid validity not declared.",
            )
        )

        rfp_min_warranty = float(state.get("rfp_min_warranty_months", 12) or 12)
        warranty = float(state.get("warranty_months", 0) or 0)
        passed = warranty >= rfp_min_warranty if warranty else False
        checks.append(
            _check(
                "CONT-2",
                f"Warranty ({warranty:.0f}mo) meets RFP minimum ({rfp_min_warranty:.0f}mo)",
                passed=passed,
                severity=HIGH if not passed else LOW,
                detail=f"Warranty {warranty:.0f}mo vs required {rfp_min_warranty:.0f}mo."
                if warranty
                else "Warranty not declared.",
            )
        )
        return QAAuditCategory(
            category="CONTRACTUAL",
            checks=checks,
            passed_count=sum(1 for c in checks if c.passed),
            failed_count=sum(1 for c in checks if not c.passed),
            fatal_count=sum(1 for c in checks if not c.passed and c.severity == FATAL),
            fully_passed=all(c.passed for c in checks),
        )

    @staticmethod
    def audit_proposal(state: Dict[str, Any]) -> QAAuditCategory:
        """Proposal chapters, tables, signature blocks complete."""
        checks: List[QACheckItem] = []

        artifacts = state.get("proposal_artifacts", {}) or {}
        pdf_ok = bool(artifacts.get("pdf"))
        docx_ok = bool(artifacts.get("docx"))
        checks.append(
            _check(
                "PROP-1",
                "Proposal PDF + DOCX artifacts generated",
                passed=pdf_ok and docx_ok,
                severity=HIGH if not (pdf_ok and docx_ok) else LOW,
                detail=f"pdf={'yes' if pdf_ok else 'no'} docx={'yes' if docx_ok else 'no'}.",
            )
        )

        narrative = str(artifacts.get("narrative", "") or artifacts.get("chapters", "") or "")
        missing_chapters = [c for c in REQUIRED_CHAPTERS if c.lower() not in narrative.lower()]
        checks.append(
            _check(
                "PROP-2",
                "All proposal chapters present",
                passed=not missing_chapters,
                severity=FATAL if missing_chapters else LOW,
                detail=f"Missing: {', '.join(missing_chapters)}" if missing_chapters else "All chapters present.",
            )
        )

        signatures = state.get("signature_blocks", []) or []
        checks.append(
            _check(
                "PROP-3",
                "Signature blocks complete (authorized signatories)",
                passed=len(signatures) >= 1,
                severity=FATAL if not signatures else LOW,
                detail=f"{len(signatures)} signature blocks recorded." if signatures else "No signature blocks.",
            )
        )
        return QAAuditCategory(
            category="PROPOSAL",
            checks=checks,
            passed_count=sum(1 for c in checks if c.passed),
            failed_count=sum(1 for c in checks if not c.passed),
            fatal_count=sum(1 for c in checks if not c.passed and c.severity == FATAL),
            fully_passed=all(c.passed for c in checks),
        )

    @staticmethod
    def run_full_audit(state: Dict[str, Any], project_id: int | None = None) -> PreSubmissionReport:
        """Run all five audit categories and assemble the report."""
        categories = [
            PreSubmissionAuditor.audit_sbc_structural(state),
            PreSubmissionAuditor.audit_arithmetic(state),
            PreSubmissionAuditor.audit_attachments(state),
            PreSubmissionAuditor.audit_contractual(state),
            PreSubmissionAuditor.audit_proposal(state),
        ]

        total_checks = sum(len(c.checks) for c in categories)
        passed_checks = sum(c.passed_count for c in categories)
        failed_checks = sum(c.failed_count for c in categories)
        fatal_flaws = [check for cat in categories for check in cat.checks if not check.passed and check.severity == FATAL]

        # Bid readiness score: passed checks weighted by total (100% = fully ready).
        readiness = (passed_checks / total_checks * 100.0) if total_checks else 0.0

        blocking_issues = [
            f"{c.check_id}: {c.description} — {c.detail}" for c in fatal_flaws
        ]
        is_cleared = failed_checks == 0

        return PreSubmissionReport(
            project_id=project_id,
            categories=categories,
            bid_readiness_score=round(readiness, 2),
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            fatal_flaws=fatal_flaws,
            blocking_issues=blocking_issues,
            is_cleared_for_submission=is_cleared,
        )
