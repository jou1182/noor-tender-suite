"""
Token Budgeting & Cost Cap — Pydantic schemas.

Typed contracts for project budget configuration, consumption records, policy
state, and director override requests.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectBudgetConfig(BaseModel):
    """Per-project LLM budget configuration."""

    project_id: Optional[int] = None
    allocated_cap_usd: float = 0.0
    allocated_cap_sar: float = 0.0
    currency: str = "USD"
    soft_cap_pct: float = 80.0
    critical_pct: float = 95.0
    hard_cap_pct: float = 100.0


class BudgetConsumptionRecord(BaseModel):
    """One ledger entry for token/financial expenditure."""

    project_id: int = 0
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    timestamp: str = ""


class CostPolicyState(BaseModel):
    """Current budget policy tier and consumption."""

    project_id: int = 0
    allocated_cap_usd: float = 0.0
    consumed_usd: float = 0.0
    consumed_pct: float = 0.0
    policy_tier: str = "NORMAL"  # NORMAL | SOFT_CAP | CRITICAL | HARD_CAP
    blocked: bool = False
    override_active: bool = False
    ledger: List[BudgetConsumptionRecord] = Field(default_factory=list)


class BudgetOverrideRequest(BaseModel):
    """Director-authorized budget override."""

    project_id: int = 0
    requested_by: str = ""
    role: str = "TENDER_DIRECTOR"
    approval_signature: str = ""
    new_cap_usd: Optional[float] = None
    one_time_tokens: Optional[int] = None
    reason: str = ""
