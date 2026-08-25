"""
Agent Swarm Registry & Big-Data Ingestion — Pydantic schemas.

Typed contracts for declarative agent configuration, the swarm registry,
big-data ingest tasks, and deep compliance audit reports.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentConfiguration(BaseModel):
    """One agent's declarative configuration (from swarm_registry.yaml)."""

    id: str = ""
    name: str = ""
    model_provider: str = "cloud_openai"  # local_ollama | cloud_openai | cloud_anthropic
    model: str = "gpt-4-turbo"
    system_prompt: str = ""
    tools: List[str] = Field(default_factory=list)
    lora_adapter: Optional[str] = None
    enabled: bool = True
    alias: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SwarmRegistrySchema(BaseModel):
    """The full declarative swarm registry."""

    version: str = "1.0"
    default_model: str = "gpt-4-turbo"
    agents: List[AgentConfiguration] = Field(default_factory=list)


class BigDataIngestTask(BaseModel):
    """A bulk ingestion task specification."""

    task_id: str = ""
    project_id: str = ""
    root_directory: str = ""
    sub_disciplines: List[str] = Field(default_factory=list)
    file_types: List[str] = Field(default_factory=lambda: [".pdf", ".xlsx", ".txt", ".log"])
    chunk_partition: Dict[str, str] = Field(default_factory=dict)  # namespace fields


class DeepAuditReport(BaseModel):
    """Discrepancy report from the deep bid-vs-Owner cross-audit."""

    project_id: Optional[str] = None
    chapters_audited: int = 0
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)
    unaddressed_soil_conditions: List[str] = Field(default_factory=list)
    omitted_spec_requirements: List[str] = Field(default_factory=list)
    outdated_addenda: List[str] = Field(default_factory=list)
    overall_verdict: str = "REVIEW REQUIRED"
