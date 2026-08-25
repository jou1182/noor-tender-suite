"""Agent Registry API — dynamic agent management."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.platform_models import AgentEntry, LLMProvider

router = APIRouter()


@router.get("")
def list_agents(db: Session = Depends(get_db)):
    agents = db.query(AgentEntry).order_by(AgentEntry.execution_order).all()
    providers = {p.id: p.name for p in db.query(LLMProvider).all()}
    return {
        "agents": [
            {
                "id": a.id,
                "key": a.key,
                "name_ar": a.name_ar,
                "name_en": a.name_en,
                "avatar_emoji": a.avatar_emoji,
                "role": a.role,
                "pipeline_type": a.pipeline_type,
                "system_prompt": a.system_prompt,
                "provider_id": a.provider_id,
                "provider_name": providers.get(a.provider_id),
                "model_override": a.model_override,
                "temperature": a.temperature,
                "enabled": a.enabled,
                "execution_order": a.execution_order,
            }
            for a in agents
        ]
    }


@router.put("/{agent_key}")
def update_agent(agent_key: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    agent = db.query(AgentEntry).filter(AgentEntry.key == agent_key).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    for field in ("name_ar", "name_en", "avatar_emoji", "role", "system_prompt", "model_override"):
        if field in body:
            setattr(agent, field, body[field])
    if "provider_id" in body:
        agent.provider_id = int(body["provider_id"]) if body["provider_id"] else None
    if "temperature" in body:
        agent.temperature = float(body["temperature"])
    if "enabled" in body:
        agent.enabled = bool(body["enabled"])
    if "execution_order" in body:
        agent.execution_order = int(body["execution_order"])
    if "pipeline_type" in body:
        if body["pipeline_type"] not in ("technical", "financial", "drafting", "shared"):
            raise HTTPException(status_code=422, detail="invalid pipeline_type")
        agent.pipeline_type = body["pipeline_type"]
    db.commit()
    db.refresh(agent)
    return {"updated": agent.key, "name_en": agent.name_en, "enabled": agent.enabled}


@router.post("/{agent_key}/preview")
def preview_agent(agent_key: str, body: Dict[str, Any], db: Session = Depends(get_db)):
    """
    غرفة تدريب الوكلاء — يجرّب هوية الوكيل المعدّلة (برومبت/اسم/نموذج) فعلياً عبر
    بوابة الـLLM على رسالة تجريبية، دون تخزين أي شيء في السجل.
    """
    agent = db.query(AgentEntry).filter(AgentEntry.key == agent_key).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    draft = body.get("draft") or {}
    message = (body.get("message") or "").strip() or "عرّف بنفسك بدورك في هذه المنصة في سطرين."
    sample_context = (body.get("sample_context") or "")[:4000]

    # 1) اختيار المزوّد: مزوّد الوكيل إن حُدد، وإلا المزوّد الافتراضي المفعّل
    provider_id = draft.get("provider_id") or agent.provider_id
    provider = None
    if provider_id:
        provider = db.query(LLMProvider).filter(LLMProvider.id == int(provider_id)).first()
    if provider is None:
        provider = (
            db.query(LLMProvider)
            .filter(LLMProvider.enabled.is_(True))
            .order_by(LLMProvider.is_default.desc(), LLMProvider.id)
            .first()
        )
    if provider is None:
        raise HTTPException(
            status_code=409,
            detail="لا يوجد مزوّد LLM مفعّل — أضف مزيّداً وفعّله من تبويب LLM Providers أولاً",
        )

    # 2) تركيب رسالة النظام من الهوية المجرَّبة + سياق العينة الاختيارية
    system_prompt = str(draft.get("system_prompt") or agent.system_prompt or "")
    user_text = message
    if sample_context:
        user_text = f"{message}\n\n--- عينة سياق من المستندات ---\n{sample_context}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    try:
        from app.core.llm_gateway_v2 import chat

        result = chat(
            provider,
            messages,
            temperature=float(draft.get("temperature", agent.temperature)),
            model_override=str(draft.get("model_override") or agent.model_override or ""),
        )
        return {
            "agent_key": agent_key,
            "replied_as": f"{draft.get('name_en') or agent.name_en} ({draft.get('name_ar') or agent.name_ar})",
            "model": result.get("model") or provider.model,
            "usage": result.get("usage", {}),
            "reply": str(result.get("content", ""))[:4000],
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — نُظهر الخطأ للمستخدم بدل انفجار 500 صامت
        raise HTTPException(status_code=502, detail=f"Preview failed: {exc}")