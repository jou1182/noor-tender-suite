"""
Tender Technical Evaluation Agent.

Audits BOQ line items and technical specifications against mandatory project
criteria, applies a weighted technical evaluation score (0-100%) and generates
a structured `TechnicalEvaluationReport` with risks.

Weighting:
  - Structural & Code Compliance ........ 40%
  - Material Specification Match ........ 30%
  - Method Statement & Schedule ......... 30%

Pass/Fail gate: score < 70% routes to risk mitigation (see supervisor).
"""

from typing import Any, Dict, List

from app.schemas.tender_evaluation import (
    ComplianceStatus,
    EvaluationCriterion,
    TechnicalEvaluationReport,
    TenderRiskItem,
)

PASS_THRESHOLD = 70.0

CRITERIA_DEFS = [
    {"code": "STRUCTURAL_CODE", "name": "Structural & Code Compliance", "weight": 0.40},
    {"code": "MATERIAL_SPEC", "name": "Material Specification Match", "weight": 0.30},
    {"code": "METHOD_SCHEDULE", "name": "Method Statement & Schedule Feasibility", "weight": 0.30},
]


def _score_structural(state: Dict[str, Any]) -> float:
    """Structural & code compliance: standards citations, calc checks, RFP matrix."""
    checks: List[float] = []

    standards = state.get("standards_output", {}) or {}
    citations = standards.get("standards_citations") or []
    if citations:
        ok = sum(1 for c in citations if not c.get("violation"))
        checks.append(100.0 * ok / len(citations))

    calc = state.get("calculation_output", {}) or {}
    calc_checks = calc.get("checks") or []
    if calc_checks:
        ok = sum(1 for c in calc_checks if c.get("is_safe"))
        checks.append(100.0 * ok / len(calc_checks))

    rfp_matrix = state.get("rfp_compliance_matrix", {}) or {}
    if rfp_matrix.get("compliance_score") is not None:
        checks.append(float(rfp_matrix["compliance_score"]))

    return (sum(checks) / len(checks)) if checks else 50.0


def _score_material(state: Dict[str, Any]) -> float:
    """Material spec match: submittal parameter pass ratio."""
    checks: List[float] = []

    submittal = state.get("submittal_output", {}) or {}
    params = submittal.get("parameters_evaluated") or []
    if params:
        ok = sum(1 for p in params if p.get("passed"))
        checks.append(100.0 * ok / len(params))

    return (sum(checks) / len(checks)) if checks else 50.0


def _score_method_schedule(state: Dict[str, Any]) -> float:
    """Method statement & schedule feasibility: DCMA pass ratio + proposal rates."""
    checks: List[float] = []

    p6 = state.get("p6_output", {}) or {}
    metrics = (p6.get("dcma_results") or {}).get("metrics") or []
    if metrics:
        ok = sum(1 for m in metrics if m.get("passed"))
        checks.append(100.0 * ok / len(metrics))

    proposal = state.get("generated_proposal_output", []) or []
    if proposal:
        with_rate = sum(1 for p in proposal if p.get("productivity_rate"))
        checks.append(100.0 * with_rate / len(proposal))

    return (sum(checks) / len(checks)) if checks else 50.0


def _status_for(score: float) -> ComplianceStatus:
    if score >= 80.0:
        return ComplianceStatus.COMPLIANT
    if score >= 50.0:
        return ComplianceStatus.COMPLIANT_WITH_DEVIATION
    return ComplianceStatus.NON_COMPLIANT


def _risk_from_criterion(criterion: EvaluationCriterion, idx: int) -> TenderRiskItem:
    severity = "CRITICAL" if criterion.status == ComplianceStatus.NON_COMPLIANT else "HIGH"
    return TenderRiskItem(
        risk_id=f"TEV-RISK-{idx + 1}",
        category=criterion.name,
        description=f"{criterion.name} scored {criterion.score:.1f}/100 ({criterion.status.value}).",
        severity=severity,
        mitigation=f"Remediate '{criterion.name}' before submission; raise score to >= 80 to clear the gate.",
    )


def tender_evaluation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: audit the tender package and emit a weighted technical
    evaluation report. Mutates state with ``tender_evaluation``.
    """
    print("--- [AGENT] Tender Technical Evaluation ---")

    structural = _score_structural(state)
    material = _score_material(state)
    method = _score_method_schedule(state)
    raw_scores = {"STRUCTURAL_CODE": structural, "MATERIAL_SPEC": material, "METHOD_SCHEDULE": method}

    criteria: List[EvaluationCriterion] = []
    weighted_total = 0.0
    for idx, definition in enumerate(CRITERIA_DEFS):
        score = raw_scores[definition["code"]]
        weight = definition["weight"]
        weighted = round(score * weight, 2)
        weighted_total += weighted
        criteria.append(
            EvaluationCriterion(
                code=definition["code"],
                name=definition["name"],
                weight=weight,
                score=round(score, 2),
                weighted_score=weighted,
                status=_status_for(score),
                remarks=f"Computed {score:.1f}/100 at weight {weight*100:.0f}%.",
            )
        )

    overall_score = round(weighted_total, 2)
    pass_fail = overall_score >= PASS_THRESHOLD

    risks: List[TenderRiskItem] = []
    for idx, criterion in enumerate(criteria):
        if criterion.status == ComplianceStatus.NON_COMPLIANT:
            risks.append(_risk_from_criterion(criterion, idx))
        elif criterion.status == ComplianceStatus.COMPLIANT_WITH_DEVIATION:
            risks.append(
                TenderRiskItem(
                    risk_id=f"TEV-RISK-{idx + 1}",
                    category=criterion.name,
                    description=f"{criterion.name} carries deviations ({criterion.score:.1f}/100).",
                    severity="MEDIUM",
                    mitigation=f"Resolve deviations in '{criterion.name}' to reach full compliance.",
                )
            )

    if not pass_fail:
        risks.append(
            TenderRiskItem(
                risk_id="TEV-RISK-OVERALL",
                category="Overall Technical Compliance",
                description=f"Overall score {overall_score}/100 below the {PASS_THRESHOLD:.0f}% gate.",
                severity="CRITICAL",
                mitigation="Route to risk mitigation: remediate structural/material/method gaps.",
            )
        )

    report = TechnicalEvaluationReport(
        tender_id=int(state.get("tender_id", 0) or 0),
        overall_score=overall_score,
        compliance_score=overall_score,
        criteria=criteria,
        risks=risks,
        pass_fail=pass_fail,
        summary=(
            f"Technical evaluation {'PASSED' if pass_fail else 'FAILED'} at {overall_score}/100 "
            f"(gate >= {PASS_THRESHOLD:.0f}%)."
        ),
    )

    return {"tender_evaluation": report.model_dump()}


# Backward-compatible alias.
tender_evaluation_agent = tender_evaluation_node