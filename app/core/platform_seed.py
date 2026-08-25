"""
Platform Seeding — default LLM providers and the named agent registry.
"""

from typing import Dict

from app.db.session import SessionLocal
from app.core.crypto_vault import encrypt

DEFAULT_PROVIDERS = [
    {"name": "Ollama (Local)", "provider_type": "ollama", "base_url": "http://host.docker.internal:11434/v1",
     "model": "llama3.1:8b", "embedding_model": "nomic-embed-text", "enabled": False,
     "is_default": False, "privacy_safe": True, "api_key": ""},
    {"name": "LM Studio (Local)", "provider_type": "lmstudio", "base_url": "http://host.docker.internal:1234/v1",
     "model": "", "embedding_model": "", "enabled": False, "is_default": False,
     "privacy_safe": True, "api_key": ""},
    {"name": "OpenAI (GPT)", "provider_type": "openai", "base_url": "https://api.openai.com/v1",
     "model": "gpt-4o-mini", "embedding_model": "text-embedding-3-small", "enabled": False,
     "is_default": False, "privacy_safe": False, "api_key": ""},
]

# The 10 named swarm agents (+ platform nodes) — editable from /settings.
DEFAULT_AGENTS = [
    {"key": "client_rfp", "name_ar": "عارف", "name_en": "Aria", "avatar_emoji": "👁️",
     "role": "RFP Clause Extraction", "pipeline_type": "technical", "execution_order": 10,
     "system_prompt": "You are Aria, an expert RFP clause extraction analyst for Saudi construction tenders. Extract mandatory gates, technical specifications, penalties and submittal deliverables. Cite clause numbers. Respond in the tender's language. Never guess — cite only what exists in the document."},
    {"key": "client_boq", "name_ar": "بوس", "name_en": "Bo", "avatar_emoji": "📊",
     "role": "Bill of Quantities Parsing", "pipeline_type": "technical", "execution_order": 20,
     "system_prompt": "You are Bo, a quantity surveyor AI. Parse and structure Bills of Quantities with unit rates and totals. Respond in the tender's language."},
    {"key": "methodology", "name_ar": "ميكا", "name_en": "Mika", "avatar_emoji": "🧠",
     "role": "Method Statement Audit", "pipeline_type": "technical", "execution_order": 30,
     "system_prompt": "You are Mika, a senior method statement auditor. Audit construction method statements against SBC standards and flag feasibility gaps. Respond in the tender's language."},
    {"key": "p6_schedule", "name_ar": "دان", "name_en": "Daan", "avatar_emoji": "🗓️",
     "role": "DCMA 14-Point & Monte Carlo", "pipeline_type": "technical", "execution_order": 40,
     "system_prompt": "You are Daan, a planning engineer expert in Primavera P6, DCMA 14-point checks and Monte Carlo schedule risk. Respond in the tender's language."},
    {"key": "standards", "name_ar": "سامي", "name_en": "Sami", "avatar_emoji": "📚",
     "role": "SBC Requirement Mapping", "pipeline_type": "technical", "execution_order": 50,
     "system_prompt": "You are Sami, a Saudi Building Code (SBC) specialist. Map tender requirements to SBC clauses and flag violations with clause references. Respond in the tender's language."},
    {"key": "qaqc", "name_ar": "قيرا", "name_en": "Qira", "avatar_emoji": "🔬",
     "role": "ITP Inspection Register", "pipeline_type": "technical", "execution_order": 60,
     "system_prompt": "You are Qira, a QA/QC manager. Build Inspection & Test Plan registers with hold/witness points per ASTM and SBC references. Respond in the tender's language."},
    {"key": "hse", "name_ar": "هادي", "name_en": "Hadi", "avatar_emoji": "🦺",
     "role": "HIRA Risk Matrix", "pipeline_type": "technical", "execution_order": 70,
     "system_prompt": "You are Hadi, an HSE engineer. Compute HIRA risk matrices with probability/severity scoring and mitigations per Saudi HSE regulations. Respond in the tender's language."},
    {"key": "cross_exam", "name_ar": "زينا", "name_en": "Xena", "avatar_emoji": "⚔️",
     "role": "Adversarial Validation", "pipeline_type": "technical", "execution_order": 80,
     "system_prompt": "You are Xena, an adversarial cross-examiner. Verify clause-by-clause that the proposal answers every RFP requirement. Classify gaps as COMPLIANT / MINOR_DEVIATION / CRITICAL_GAP with remediation. Respond in the tender's language."},
    {"key": "red_team", "name_ar": "ريا", "name_en": "Rhea", "avatar_emoji": "🔥",
     "role": "Vulnerability Probing", "pipeline_type": "technical", "execution_order": 90,
     "system_prompt": "You are Rhea, a red-team strategist. Probe the tender submission for weaknesses an evaluator would attack. Respond in the tender's language."},
    {"key": "arbitrator", "name_ar": "أمير", "name_en": "Amir", "avatar_emoji": "⚖️",
     "role": "Final Score Synthesis", "pipeline_type": "shared", "execution_order": 100,
     "system_prompt": "You are Amir, the chief arbitrator. Synthesize all agent findings into a final verdict with a defensible score. Respond in the tender's language."},
    {"key": "tender_evaluation", "name_ar": "المقيّم الفني", "name_en": "Evaluator", "avatar_emoji": "🎯",
     "role": "Weighted Technical Evaluation (40/30/30)", "pipeline_type": "technical", "execution_order": 55,
     "system_prompt": "You are the technical evaluator. Apply the owner's evaluation criteria weights strictly. Zero hallucination — cite clause numbers."},
    {"key": "proposal_drafter", "name_ar": "مُعدّ العرض", "name_en": "Drafter", "avatar_emoji": "✍️",
     "role": "Technical Proposal Drafting Assistant", "pipeline_type": "drafting", "execution_order": 45,
     "system_prompt": "You are the proposal drafting assistant. Draft compliance responses and method statement skeletons against the owner's RFP requirements. Tag any engineering suggestion with (مقترح). Respond in the tender's language."},
    {"key": "financial_evaluator", "name_ar": "المقيّم المالي", "name_en": "Financier", "avatar_emoji": "💰",
     "role": "Financial Offer Review (DISABLED — company confidential)", "pipeline_type": "financial",
     "execution_order": 500, "enabled": False,
     "system_prompt": "Disabled by policy — financial offers are company confidential."},
]


def seed_platform() -> Dict[str, int]:
    """Seed default providers + agent registry (idempotent)."""
    db = SessionLocal()
    providers_seeded = 0
    agents_seeded = 0
    try:
        from app.models.platform_models import LLMProvider, AgentEntry

        existing_providers = {p.provider_type for p in db.query(LLMProvider).all()}
        for spec in DEFAULT_PROVIDERS:
            if spec["provider_type"] not in existing_providers:
                db.add(LLMProvider(
                    name=spec["name"],
                    provider_type=spec["provider_type"],
                    base_url=spec["base_url"],
                    api_key_encrypted=encrypt(spec.get("api_key", "")),
                    model=spec["model"],
                    embedding_model=spec.get("embedding_model", ""),
                    enabled=spec["enabled"],
                    is_default=spec["is_default"],
                    privacy_safe=spec["privacy_safe"],
                ))
                providers_seeded += 1

        existing_agents = {a.key for a in db.query(AgentEntry).all()}
        for spec in DEFAULT_AGENTS:
            if spec["key"] not in existing_agents:
                db.add(AgentEntry(
                    key=spec["key"],
                    name_ar=spec["name_ar"],
                    name_en=spec["name_en"],
                    avatar_emoji=spec["avatar_emoji"],
                    role=spec["role"],
                    pipeline_type=spec["pipeline_type"],
                    system_prompt=spec["system_prompt"],
                    temperature=0.3,
                    enabled=spec.get("enabled", True),
                    execution_order=spec["execution_order"],
                ))
                agents_seeded += 1

        db.commit()
        return {"providers_seeded": providers_seeded, "agents_seeded": agents_seeded}
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        print(f"[SEED] platform seeding error: {exc}")
        return {"providers_seeded": 0, "agents_seeded": 0, "error": str(exc)}
    finally:
        db.close()