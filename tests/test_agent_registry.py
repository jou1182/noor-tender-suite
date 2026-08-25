"""
Agent Registry — verification tests (seeding, updates, enable/disable).
"""

from app.agents.value_engineering_agent import value_engineering_node
from app.core.platform_seed import DEFAULT_AGENTS, DEFAULT_PROVIDERS, seed_platform
from app.db.session import SessionLocal
from app.models.platform_models import AgentEntry, LLMProvider


def _fresh_db():
    """Yield a session after ensuring tables + seed ran once."""
    from app.db.base import Base
    from app.db.session import engine

    Base.metadata.create_all(bind=engine)
    seed_platform()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_seed_creates_all_named_agents():
    db = next(_fresh_db())
    agents = db.query(AgentEntry).all()
    keys = {a.key for a in agents}
    for expected in ["client_rfp", "client_boq", "methodology", "p6_schedule", "standards",
                     "qaqc", "hse", "cross_exam", "red_team", "arbitrator"]:
        assert expected in keys, f"missing seeded agent: {expected}"
    assert len(agents) >= 10


def test_seed_is_idempotent():
    db = next(_fresh_db())
    before = db.query(AgentEntry).count()
    result = seed_platform()
    after = db.query(AgentEntry).count()
    assert after == before, "seed duplicated agents"
    assert result["agents_seeded"] == 0


def test_seed_creates_local_providers():
    db = next(_fresh_db())
    providers = {p.provider_type for p in db.query(LLMProvider).all()}
    assert "ollama" in providers
    assert "lmstudio" in providers


def test_agent_update_fields():
    db = next(_fresh_db())
    agent = db.query(AgentEntry).filter(AgentEntry.key == "cross_exam").first()
    original_name = agent.name_en

    agent.name_en = "Xena Prime"
    agent.model_override = "qwen2.5:14b"
    agent.enabled = False
    db.commit()
    db.refresh(agent)

    assert agent.name_en == "Xena Prime"
    assert agent.model_override == "qwen2.5:14b"
    assert agent.enabled is False

    # restore
    agent.name_en = original_name
    agent.model_override = ""
    agent.enabled = True
    db.commit()


def test_disabled_agent_excluded_from_active_queries():
    db = next(_fresh_db())
    agent = db.query(AgentEntry).filter(AgentEntry.key == "financial_evaluator").first()
    assert agent is not None
    assert agent.enabled is False, "financial evaluator must ship disabled (company confidential)"


def test_default_agents_have_system_prompts():
    db = next(_fresh_db())
    for agent in db.query(AgentEntry).filter(AgentEntry.enabled.is_(True)).all():
        assert agent.system_prompt.strip(), f"{agent.key} missing system prompt"


def test_seed_constants_consistency():
    keys = [a["key"] for a in DEFAULT_AGENTS]
    assert len(keys) == len(set(keys)), "duplicate agent keys in seed"
    assert len(keys) >= 10, "fewer than 10 agents seeded"
    assert all(a["system_prompt"].strip() for a in DEFAULT_AGENTS)
    assert all(p["base_url"] for p in DEFAULT_PROVIDERS)