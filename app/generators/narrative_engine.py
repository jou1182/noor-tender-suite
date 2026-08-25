"""
Narrative Engine & Templating.

Assembles the technical proposal narrative from LangGraph state using jinja2
templates. Produces:

  - Executive summary + project scope narrative
  - VE replacement justifications (SBC-304 clause references + badges)
  - SBC compliance register narrative
  - Standard engineering method statements derived from project scope
"""

from datetime import datetime
from typing import Any, Dict, List

from jinja2 import Environment, BaseLoader

NARRATIVE_TEMPLATE = """
{{ "=" * 70 }}
{{ project.name | upper }}
Technical Proposal Narrative — {{ project.client }}
Tender Reference: {{ project.tender_reference }} | Generated {{ generated_at }}
{{ "=" * 70 }}

1. EXECUTIVE SUMMARY
----------------------
{{ summary }}

2. PROJECT SCOPE & PARAMETERS
-----------------------------
{% if project.scope %}{{ project.scope }}{% else %}Standard scope of works per tender
package and technical specification.{% endif %}

3. VALUE ENGINEERING PROPOSALS
------------------------------
{% for ve in ve_proposals %}
VE-{{ loop.index }}: {{ ve.boq_item }} -> {{ ve.proposed_alternative }}
  Status: {{ ve.sbc_status }}
  {% if ve.sbc_status == 'COMPLIANT' %}[SBC COMPLIANT]{% else %}[BLOCKED BY SBC 304]{% endif %}
  Justification: {{ ve.technical_justification }}
  SBC-304 References: {{ ve.sbc_304_references | join(', ') }}
  Net Savings: SAR {{ '%.2f' | format(ve.net_savings_sar) }}
{% else %}
No value-engineering candidates evaluated.
{% endfor %}

4. SBC-304 COMPLIANCE REGISTER
------------------------------
{% for c in compliance %}
  {{ c.clause_code }} [{{ c.status }}] — {{ c.requirement }}
    {{ c.gap_analysis }}
{% else %}
No compliance verdicts recorded.
{% endfor %}

5. ENGINEERING METHOD STATEMENTS
--------------------------------
{% for m in method_statements %}
M-{{ loop.index }}: {{ m.title }}
  {{ m.content }}
{% endfor %}

6. RISK REGISTER
----------------
{% for r in risks %}
  {{ r.risk_id }} [{{ r.severity }}] {{ r.category }} — {{ r.mitigation }}
{% else %}
No material risks outstanding.
{% endfor %}

7. TECHNICAL EVALUATION
-----------------------
Overall Score: {{ evaluation.overall_score }}/100
Pass/Fail: {{ 'PASS' if evaluation.pass_fail else 'FAIL' }}
Summary: {{ evaluation.summary }}
"""

EXECUTIVE_SUMMARY_TEMPLATE = """
This technical proposal responds to {{ project.client }}'s tender
{{ project.tender_reference }} for {{ project.name }}. The submission achieves
an overall technical evaluation score of {{ evaluation.overall_score }}/100
({{ 'PASS' if evaluation.pass_fail else 'FAIL' }}) and identifies
{{ ve_proposals | length }} value-engineering opportunities worth an estimated
SAR {{ '%.2f' | format(ve_savings_total) }} in net savings, all verified
against SBC-304 structural compliance requirements.
"""

METHOD_STATEMENTS: Dict[str, str] = {
    "excavation": (
        "1. Site surveying and marking. 2. Utility clearance and permits. "
        "3. Mechanical excavation to required depth (comply SBC 303 geotechnical). "
        "4. Shoring/benching for depths > 1.5m. 5. Formation inspection and compaction testing."
    ),
    "concrete": (
        "1. Surface preparation and formwork installation. 2. Steel reinforcement placement "
        "per SBC 304 §6.1 fixing schedules. 3. Concrete pour with vibration (w/c per exposure "
        "class, SBC 304 §5.3). 4. Curing for minimum 7 days. 5. Striking and curing compound application."
    ),
    "steel": (
        "1. Shop drawing approval. 2. Cutting & bending schedule per SBC 304 §3.5.3. "
        "3. Erection sequence and temporary bracing. 4. Bolting/welding QA per project ITP. "
        "5. Surface protection and coating."
    ),
    "default": (
        "1. Mobilization and method statement approval. 2. Execution per approved drawings and "
        "specifications. 3. Quality inspection per ITP hold points. 4. Handover documentation."
    ),
}


class ProposalNarrativeEngine:
    """jinja2-driven narrative assembler for technical proposals."""

    def __init__(self) -> None:
        self._env = Environment(loader=BaseLoader(), autoescape=False, trim_blocks=True, lstrip_blocks=True)

    def _render(self, template: str, context: Dict[str, Any]) -> str:
        return self._env.from_string(template).render(**context)

    def build_context(
        self,
        project: Dict[str, Any],
        ve_proposals: List[Dict[str, Any]],
        compliance: List[Dict[str, Any]],
        risks: List[Dict[str, Any]],
        evaluation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assemble the full template context from state-derived sections."""
        return {
            "project": project,
            "ve_proposals": ve_proposals,
            "ve_savings_total": sum(float(v.get("net_savings_sar") or 0) for v in ve_proposals),
            "compliance": compliance,
            "risks": risks,
            "evaluation": evaluation,
            "method_statements": self.build_method_statements(project),
            "summary": self._render(
                EXECUTIVE_SUMMARY_TEMPLATE,
                {
                    "project": project,
                    "evaluation": evaluation,
                    "ve_proposals": ve_proposals,
                    "ve_savings_total": sum(float(v.get("net_savings_sar") or 0) for v in ve_proposals),
                },
            ),
            "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }

    def render_narrative(self, context: Dict[str, Any]) -> str:
        """Render the full proposal narrative text (used by both DOCX and PDF)."""
        return self._render(NARRATIVE_TEMPLATE, context)

    def build_method_statements(self, project: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate standard engineering method statements from scope parameters."""
        scope = (project.get("scope") or "").lower()
        titles: List[Dict[str, str]] = []
        if "excavat" in scope or "earthwork" in scope or "grading" in scope:
            titles.append({"title": "Earthworks & Excavation Method Statement", "content": METHOD_STATEMENTS["excavation"]})
        if "concrete" in scope or "structure" in scope or "foundation" in scope:
            titles.append({"title": "Structural Concrete Method Statement", "content": METHOD_STATEMENTS["concrete"]})
        if "steel" in scope or "structural steel" in scope:
            titles.append({"title": "Structural Steel Erection Method Statement", "content": METHOD_STATEMENTS["steel"]})
        if not titles:
            titles.append({"title": "General Works Method Statement", "content": METHOD_STATEMENTS["default"]})
        return titles

    def ve_justification(self, card: Dict[str, Any]) -> str:
        """Dynamic SBC-304 badge + justification narrative for a VE card."""
        status = card.get("sbc_status", "BLOCKED")
        badge = "[SBC COMPLIANT] " if status == "COMPLIANT" else "[BLOCKED BY SBC 304] "
        refs = ", ".join(card.get("sbc_304_references", []) or [])
        return (
            f"{badge}{card.get('technical_justification', 'No justification provided.')} "
            f"References: {refs}."
        )
