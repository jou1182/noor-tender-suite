"""
Model Evaluation & Benchmarking — Pydantic schemas.

Typed contracts for golden benchmark test cases, per-model performance records,
the comparative leaderboard, and routing recommendations.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BenchmarkTestCase(BaseModel):
    """A golden ground-truth evaluation case."""

    case_id: str
    task_type: str  # SBC_304 | BOQ_EXTRACTION | FIDIC_RISK
    prompt: str
    expected_output: str
    numeric_checks: List[Dict[str, Any]] = Field(default_factory=list)  # [{field, expected}]


class ModelPerformanceRecord(BaseModel):
    """Scored performance for one model endpoint on the benchmark suite."""

    model_name: str
    provider: str = "cloud"  # cloud | local
    endpoint: str = ""
    accuracy: float = 0.0
    f1_score: float = 0.0
    numeric_exact_match: float = 0.0
    avg_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    cost_per_1k_tokens_usd: float = 0.0
    total_cases: int = 0
    passed_cases: int = 0


class ComparativeLeaderboard(BaseModel):
    """Sorted accuracy-vs-cost leaderboard across evaluated models."""

    records: List[ModelPerformanceRecord] = Field(default_factory=list)
    best_accuracy_model: str = ""
    best_cost_effective_model: str = ""
    generated_at: str = ""


class ModelRoutingRecommendation(BaseModel):
    """Heuristic: recommend local model when it matches >=95% of frontier."""

    task_type: str
    recommended_model: str
    local_selected: bool = False
    frontier_accuracy: float = 0.0
    local_accuracy: float = 0.0
    rationale: str = ""
