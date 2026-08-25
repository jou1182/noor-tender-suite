"""
Schedule Analytics — Pydantic schemas.

Typed contracts for schedule parsing, CPM analytics, DCMA auditing, and
BOQ-to-schedule linkage. Mirrored conceptually by the frontend schedule studio.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScheduleActivity(BaseModel):
    """A single schedule activity with CPM-computed dates and floats."""

    task_id: str
    name: str
    wbs: str = ""
    duration_days: float = 0.0
    early_start: Optional[float] = None  # days from project start
    early_finish: Optional[float] = None
    late_start: Optional[float] = None
    late_finish: Optional[float] = None
    total_float: Optional[float] = None
    free_float: Optional[float] = None
    is_critical: bool = False
    constraint_type: str = "As Soon As Possible"
    lag: float = 0.0
    predecessors: List[str] = Field(default_factory=list)
    successors: List[str] = Field(default_factory=list)
    original_duration: float = 0.0


class ScheduleRelationship(BaseModel):
    """A predecessor/successor relationship between activities."""

    pred_task_id: str
    succ_task_id: str
    lag: float = 0.0
    rel_type: str = "FS"  # FS | SS | FF | SF


class DCMAMetric(BaseModel):
    """One DCMA 14-point check result."""

    check: str
    value_pct: float
    threshold: float
    passed: bool
    description: str = ""


class DCMAAuditReport(BaseModel):
    """Full DCMA 14-point schedule health audit."""

    overall_status: str = "FAILED"
    total_activities: int = 0
    metrics: List[DCMAMetric] = Field(default_factory=list)
    schedule_quality_index: float = 0.0  # SQI 0-100
    contract_duration_days: Optional[float] = None
    planned_duration_days: Optional[float] = None
    duration_variance_pct: Optional[float] = None
    ld_risk_flag: bool = False


class ScheduleSummary(BaseModel):
    """Aggregate schedule summary for state injection."""

    activity_count: int = 0
    critical_activities: int = 0
    critical_path_duration_days: float = 0.0
    total_float_min: Optional[float] = None
    total_float_max: Optional[float] = None
    average_float: Optional[float] = None
    missing_logic_activities: int = 0
    hard_constrained_activities: int = 0
    boq_linkage_count: int = 0


class ScheduleAnalysis(BaseModel):
    """Top-level schedule analysis bundle written to state."""

    activities: List[ScheduleActivity] = Field(default_factory=list)
    relationships: List[ScheduleRelationship] = Field(default_factory=list)
    summary: ScheduleSummary = Field(default_factory=ScheduleSummary)
    dcma_report: DCMAAuditReport = Field(default_factory=DCMAAuditReport)
    boq_linkage: Dict[str, Any] = Field(default_factory=dict)
