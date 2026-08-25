from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ClientRfpOutput(BaseModel):
    extracted_requirements: List[Dict[str, Any]] = Field(default_factory=list)

class ClientBoqOutput(BaseModel):
    boq_financials: Dict[str, Any] = Field(default_factory=dict)

class MethodologyOutput(BaseModel):
    methodology_findings: List[Dict[str, Any]] = Field(default_factory=list)

class P6ScheduleOutput(BaseModel):
    schedule_audit: Dict[str, Any] = Field(default_factory=dict)

class StandardsComplianceOutput(BaseModel):
    standards_citations: List[Dict[str, Any]] = Field(default_factory=list)

class QAQCOutput(BaseModel):
    qaqc_deficiencies: List[Dict[str, Any]] = Field(default_factory=list)

class HSEOutput(BaseModel):
    hse_risks: List[Dict[str, Any]] = Field(default_factory=list)

class DiscrepancyOutput(BaseModel):
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)

class RedTeamOutput(BaseModel):
    red_team_feedback: List[Dict[str, Any]] = Field(default_factory=list)
    rfi_drafts: List[str] = Field(default_factory=list)

class EtimadOutput(BaseModel):
    status: str
    readiness_score: float
    local_content_score: float
    missing_mandatory_attachments: List[str]

class ArbitratorFinalOutput(BaseModel):
    final_score: float
    summary: str
    status: str
