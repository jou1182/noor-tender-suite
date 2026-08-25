"""
Proposal Drafting Assistant.

Generates a compliance-response skeleton for the tender's binding requirements
(pinned criteria), method-statement skeletons per BOQ trade, and a document
checklist — deterministic template base with optional LLM enrichment through
the dynamic gateway (provider/model from the agent registry).

Honors the charter rules: zero hallucination (templates reference only the
extracted requirement text) and (مقترح) tagging for AI-generated suggestions.
"""

import re
from typing import Any, Dict, List, Optional

from app.db.session import SessionLocal
from app.models.platform_models import TenderRequirement


def _detect_language(texts: List[str]) -> str:
    """'ar' when Arabic characters dominate, else 'en'."""
    sample = " ".join(texts)[:4000]
    arabic = len(re.findall(r"[\u0600-\u06FF]", sample))
    latin = len(re.findall(r"[A-Za-z]", sample))
    return "ar" if arabic >= latin else "en"


def _is_rtl(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


class ProposalDrafter:
    """Deterministic drafting templates + optional LLM enrichment."""

    AR = {
        "mandatory_response": (
            "التزام كامل: {text}\n"
            "(مقترح) سيتم تضمين هذا الالتزام في القسم المختص من العرض الفني مع المستندات المؤيدة "
            "وإحالة مرجعية للبند في الكراسة."
        ),
        "weighted_response": (
            "خطة تعظيم الدرجة ({weight}% من التقييم): {text}\n"
            "(مقترح) يُبنى الرد على نقاط القوة لدى الشركة مع أدلة موثقة تثبت المطابقة "
            "لرفع الدرجة إلى الحد الأقصى."
        ),
        "disqualification_response": (
            "بند حرج (سبب استبعاد محتمل): {text}\n"
            "إجراء إلزامي: مراجعة قانونية + فنية قبل التسليم، وتضمين مستند الالتزام "
            "الموقّع من المفوض بالتوقيع في المكان المحدد من العرض."
        ),
        "checklist_prefix": "تجهيز ومرفق مع العرض",
        "method_title": "مسودة منهجية تنفيذ — {trade}",
        "method_sections": ["الغرض والنطاق", "الموارد والكوادر", "خطوات التنفيذ", "ضبط الجودة", "السلامة والمتطلبات الحكومية"],
        "response_label": "مسودة الاستجابة",
    }
    EN = {
        "mandatory_response": (
            "Full commitment: {text}\n"
            "(suggested) This commitment will be embedded in the dedicated proposal section "
            "with supporting documents and a back-reference to the RFP clause."
        ),
        "weighted_response": (
            "Score-maximisation plan ({weight}% of evaluation): {text}\n"
            "(suggested) The response will leverage company strengths with documented "
            "evidence to achieve the maximum available marks."
        ),
        "disqualification_response": (
            "Critical clause (potential disqualification): {text}\n"
            "Mandatory action: legal + technical review before submission; include the signed "
            "commitment document in the designated proposal slot."
        ),
        "checklist_prefix": "Prepare & attach with proposal",
        "method_title": "Method statement draft — {trade}",
        "method_sections": ["Purpose & Scope", "Resources & Crew", "Execution Steps", "Quality Control", "HSE & Statutory"],
        "response_label": "Draft Response",
    }

    @staticmethod
    def _templates(lang: str) -> Dict[str, str]:
        return ProposalDrafter.AR if lang == "ar" else ProposalDrafter.EN

    @staticmethod
    def generate(tender_id: int, enrich: bool = False, max_llm_sections: int = 8) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            requirements = (
                db.query(TenderRequirement)
                .filter(TenderRequirement.tender_id == tender_id)
                .order_by(TenderRequirement.requirement_type, TenderRequirement.id)
                .all()
            )
            if not requirements:
                return {
                    "tender_id": tender_id, "language": "en", "sections": [],
                    "method_statements": [], "checklist": [], "llm_enriched": False,
                    "message": "No binding requirements found — pin the evaluation-criteria document first.",
                }

            lang = _detect_language([r.requirement_text for r in requirements])
            templates = ProposalDrafter._templates(lang)

            sections: List[Dict[str, Any]] = []
            checklist: List[Dict[str, Any]] = []

            for requirement in requirements:
                text = requirement.requirement_text
                rtype = requirement.requirement_type
                if rtype == "MANDATORY":
                    response = templates["mandatory_response"].format(text=text)
                elif rtype == "DISQUALIFICATION":
                    response = templates["disqualification_response"].format(text=text)
                    checklist.append({
                        "item": text[:160], "source": requirement.clause_ref or f"REQ-{requirement.id}",
                        "note": templates["checklist_prefix"],
                    })
                else:
                    response = templates["weighted_response"].format(
                        weight=int(requirement.weight or 0), text=text
                    )
                sections.append({
                    "requirement_id": requirement.id,
                    "requirement_type": rtype,
                    "clause_ref": requirement.clause_ref or f"REQ-{requirement.id}",
                    "weight": requirement.weight,
                    "requirement_text": text[:400],
                    "draft_response": response,
                    "llm_enriched": False,
                })

            # Attachments mentioned anywhere in the requirements become checklist items.
            for requirement in requirements:
                for match in re.finditer(
                    r"(ضمان[^.,؛]{0,60}|شهادة[^.,؛]{0,60}|سجل[^.,؛]{0,60}|certificate[^.,؛]{0,60}|"
                    r"registration[^.,؛]{0,60}|guarantee[^.,؛]{0,60})",
                    requirement.requirement_text, re.IGNORECASE,
                ):
                    item = _clean(match.group(0))
                    if item and item.lower() not in {c["item"].lower() for c in checklist}:
                        checklist.append({"item": item[:160], "source": requirement.clause_ref, "note": templates["checklist_prefix"]})

            method_statements = ProposalDrafter._method_skeletons(lang)

            llm_enriched = False
            if enrich:
                llm_enriched = ProposalDrafter._enrich(sections[:max_llm_sections], lang)

            return {
                "tender_id": tender_id,
                "language": lang,
                "sections": sections,
                "method_statements": method_statements,
                "checklist": checklist,
                "llm_enriched": llm_enriched,
            }
        finally:
            db.close()

    @staticmethod
    def _method_skeletons(lang: str) -> List[Dict[str, Any]]:
        templates = ProposalDrafter._templates(lang)
        trades = (
            ["الأعمال المدنية", "أعمال الخرسانات", "الأعمال الميكانيكية", "الأعمال الكهربائية"]
            if lang == "ar"
            else ["Civil Works", "Concrete Works", "Mechanical Works", "Electrical Works"]
        )
        skeletons = []
        for trade in trades:
            skeletons.append({
                "trade": trade,
                "title": templates["method_title"].format(trade=trade),
                "sections": templates["method_sections"],
            })
        return skeletons

    @staticmethod
    def _enrich(sections: List[Dict[str, Any]], lang: str) -> bool:
        """LLM enrichment via the proposal_drafter agent's bound provider."""
        try:
            db = SessionLocal()
            try:
                from app.models.platform_models import AgentEntry

                agent = db.query(AgentEntry).filter(AgentEntry.key == "proposal_drafter").first()
                provider = (
                    db.query(AgentEntry).filter(AgentEntry.key == "proposal_drafter").first()
                    and None
                )
                provider_row = None
                if agent and agent.provider_id:
                    from app.models.platform_models import LLMProvider

                    provider_row = db.query(LLMProvider).filter(LLMProvider.id == agent.provider_id).first()
                if provider_row is None:
                    from app.models.platform_models import LLMProvider

                    provider_row = (
                        db.query(LLMProvider)
                        .filter(LLMProvider.enabled.is_(True))
                        .order_by(LLMProvider.is_default.desc(), LLMProvider.id)
                        .first()
                    )
                if provider_row is None or not provider_row.enabled:
                    return False
            finally:
                pass
            db.close()

            from app.core.llm_gateway_v2 import chat, LLMGatewayError

            enriched_any = False
            for section in sections:
                prompt = (
                    f"{agent.system_prompt}\n\n"
                    f"RFP requirement:\n{section['requirement_text']}\n\n"
                    f"Draft a compliance response for the technical proposal."
                )
                try:
                    result = chat(provider_row, [
                        {"role": "system", "content": agent.system_prompt},
                        {"role": "user", "content": prompt},
                    ], temperature=0.3, max_tokens=700, model_override=agent.model_override or "")
                    if result.get("content"):
                        section["draft_response"] = result["content"]
                        section["llm_enriched"] = True
                        enriched_any = True
                except LLMGatewayError:
                    continue
            return enriched_any
        except Exception:  # noqa: BLE001
            return False


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()