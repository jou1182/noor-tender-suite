"""LLM Providers API — dynamic multi-provider management."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.crypto_vault import decrypt, encrypt, mask
from app.core.llm_gateway_v2 import test_connection
from app.db.session import get_db
from app.models.platform_models import LLMProvider

router = APIRouter()


def _serialize(provider: LLMProvider, include_key: bool = False) -> Dict[str, Any]:
    data = {
        "id": provider.id,
        "name": provider.name,
        "provider_type": provider.provider_type,
        "base_url": provider.base_url,
        "model": provider.model,
        "embedding_model": provider.embedding_model,
        "enabled": provider.enabled,
        "is_default": provider.is_default,
        "privacy_safe": provider.privacy_safe,
        "api_key_masked": mask(decrypt(provider.api_key_encrypted or "")),
        "has_api_key": bool(provider.api_key_encrypted),
    }
    if include_key:
        data["api_key"] = decrypt(provider.api_key_encrypted or "")
    return data


@router.get("")
def list_providers(db: Session = Depends(get_db)):
    providers = db.query(LLMProvider).order_by(LLMProvider.id).all()
    return {"providers": [_serialize(p) for p in providers]}


@router.post("")
def create_provider(body: Dict[str, Any], db: Session = Depends(get_db)):
    required = ("name", "provider_type")
    if not all(body.get(field) for field in required):
        raise HTTPException(status_code=422, detail="name and provider_type are required")
    if body["provider_type"] not in ("openai", "anthropic", "google", "deepseek", "ollama", "lmstudio"):
        raise HTTPException(status_code=422, detail="unsupported provider_type")

    provider = LLMProvider(
        name=body["name"],
        provider_type=body["provider_type"],
        base_url=body.get("base_url", ""),
        api_key_encrypted=encrypt(body.get("api_key", "")),
        model=body.get("model", ""),
        embedding_model=body.get("embedding_model", ""),
        enabled=bool(body.get("enabled", False)),
        is_default=bool(body.get("is_default", False)),
        privacy_safe=body.get("provider_type") in ("ollama", "lmstudio"),
    )
    if provider.is_default:
        for other in db.query(LLMProvider).filter(LLMProvider.is_default.is_(True)):
            other.is_default = False
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return _serialize(provider)


@router.put("/{provider_id}")
def update_provider(provider_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    for field in ("name", "base_url", "model", "embedding_model"):
        if field in body:
            setattr(provider, field, body[field])
    if "provider_type" in body:
        if body["provider_type"] not in ("openai", "anthropic", "google", "deepseek", "ollama", "lmstudio"):
            raise HTTPException(status_code=422, detail="unsupported provider_type")
        provider.provider_type = body["provider_type"]
    if "api_key" in body and body["api_key"]:
        provider.api_key_encrypted = encrypt(body["api_key"])
    for flag in ("enabled", "is_default", "privacy_safe"):
        if flag in body:
            setattr(provider, flag, bool(body[flag]))
    if provider.is_default:
        for other in db.query(LLMProvider).filter(
            LLMProvider.is_default.is_(True), LLMProvider.id != provider.id
        ):
            other.is_default = False
    db.commit()
    db.refresh(provider)
    return _serialize(provider)


@router.delete("/{provider_id}")
def delete_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    db.delete(provider)
    db.commit()
    return {"deleted": provider_id}


@router.post("/{provider_id}/test")
def test_provider(provider_id: int, db: Session = Depends(get_db)):
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return test_connection(provider)