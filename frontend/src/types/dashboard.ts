/**
 * Dashboard & Workspace — TypeScript schemas mirroring backend Pydantic models
 * (app/schemas/tender_evaluation.py, app/db/models.py, project endpoints).
 */

/** Project status mirroring the persistence layer. */
export type ProjectStatus = 'draft' | 'auditing' | 'ready_for_submission' | 'submitted';

/** Client/owner of a tender package. */
export type ProjectClient = 'ROSHN' | 'Ministry of Transport' | 'Qiddiya' | 'Saudi Aramco' | 'Red Sea Global';

/** A tender project row in the portfolio data-grid. */
export interface ProjectSummary {
  id: string;
  name: string;
  client: ProjectClient;
  tender_reference: string;
  status: ProjectStatus;
  submission_due: string; // ISO date
  technical_score: number | null; // 0-100
  evaluated_value_sar: number;
  ve_opportunities_sar: number;
  sbc_compliance_rate: number | null; // 0-100
  updated_at: string;
}

/** Portfolio overview header metrics. */
export interface PortfolioMetrics {
  total_active_tenders: number;
  total_evaluated_value_sar: number;
  net_ve_opportunities_sar: number;
  overall_sbc_compliance_rate: number;
}

/** SSE event payload from `/api/v1/projects/{id}/stream`. */
export interface TenderStreamEvent {
  event: string;
  payload: Record<string, unknown>;
  ts?: number;
}

/** Live agent decision line for the terminal. */
export interface AgentLogLine {
  id: string;
  agent: string;
  message: string;
  status: 'running' | 'completed' | 'error';
  timestamp: string;
}

/** Workspace document (uploaded BOQ.xlsx / Spec.pdf). */
export interface WorkspaceDocument {
  id: string;
  filename: string;
  document_type: 'boq' | 'spec';
  status: 'uploaded' | 'parsing' | 'parsed' | 'failed';
  uploaded_at: string;
}

/** Compliance verdict row for the SBC-304 audit tab. */
export interface ComplianceVerdict {
  clause_code: string;
  requirement: string;
  status: 'COMPLIANT' | 'COMPLIANT_WITH_DEVIATION' | 'NON_COMPLIANT';
  severity: string;
  gap_analysis: string;
  sbc_section?: string;
}
