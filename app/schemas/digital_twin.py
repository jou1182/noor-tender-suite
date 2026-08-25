"""
Digital Twin Tender Simulation — Pydantic schemas.

Typed contracts for the multidimensional property graph, simulation scenario
results, and the enterprise knowledge hub summary.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TwinGraphNode(BaseModel):
    """A node in the digital twin property graph."""

    id: str
    label: str
    node_type: str  # boq | bim | schedule | sbc_rule | gis_route | fidic_clause
    properties: Dict[str, Any] = Field(default_factory=dict)


class TwinGraphEdge(BaseModel):
    """A directed edge between digital twin nodes."""

    source: str
    target: str
    relation: str  # feeds | maps_to | governed_by | delayed_by | affects
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)


class TwinGraphTopology(BaseModel):
    """The full digital twin graph topology."""

    nodes: List[TwinGraphNode] = Field(default_factory=list)
    edges: List[TwinGraphEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0


class SimulationScenarioResult(BaseModel):
    """Result of a 'what-if' Monte Carlo simulation over the graph."""

    scenario_id: str = ""
    description: str = ""
    resilience_rating: str = "MODERATE"  # HIGH | MODERATE | LOW | CRITICAL
    revised_cash_flow: List[Dict[str, Any]] = Field(default_factory=list)
    ld_exposure_probability: float = 0.0
    affected_nodes: List[str] = Field(default_factory=list)
    violations_flagged: List[Dict[str, Any]] = Field(default_factory=list)


class EnterpriseKnowledgeSummary(BaseModel):
    """Cross-tender comparative analytics from the knowledge hub."""

    tenders_indexed: int = 0
    average_concrete_consumption_m3: float = 0.0
    regional_benchmarks: Dict[str, Any] = Field(default_factory=dict)
    lessons_learned_count: int = 0
