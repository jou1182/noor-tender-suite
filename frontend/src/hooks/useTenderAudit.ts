import { useState, useEffect, useCallback } from 'react';
import { ComplianceRecord } from '../components/ComplianceMatrixTable';
import { Discrepancy } from '../components/DiscrepancyMatrixTable';
import { EtimadData } from '../components/EtimadReadinessCard';
import { DriftData } from '../components/AddendumDiffViewer';
import { EngineeringCheck } from '../components/EngineeringCalculationCard';
import { MethodStatement } from '../components/ProposalBuilderStudio';
import { ContractRisk } from '../components/ContractRiskMatrixTable';
import { ClaimsData } from '../components/ClaimsStudio';
import { LlmMetrics } from '../components/LlmUsageCard';
import { BimData } from '../components/BimModelViewer';
import { InstitutionalMemoryData } from '../components/WinLossAnalyticsCard';
import { ProcurementData } from '../components/ProcurementStudio';
import { ScheduleHealthData } from '../components/ScheduleHealthStudio';
import { QaQcHseData } from '../components/ItpHseStudio';
import { DossierData } from '../components/MasterExportStudio';
import { fetchTenderStatus } from '../lib/api_client';
import { TenantContext } from '../lib/demoData';

export interface Vulnerability {
  risk_type: string;
  description: string;
  severity: "High" | "Medium" | "Low";
  mitigation: string;
}

export interface AuditMetadata {
  institutional_memory_output?: InstitutionalMemoryData;
  generated_proposal_output?: MethodStatement[];
  red_team_feedback?: Vulnerability[];
  rfi_drafts?: string[];
  discrepancy_output?: { discrepancies: Discrepancy[] };
  etimad_output?: EtimadData;
  drift_output?: DriftData;
  calculation_output?: { checks: EngineeringCheck[] };
  geotech_output?: any;
  p6_output?: ScheduleHealthData;
  commercial_output?: any;
  vendor_output?: ProcurementData;
  qaqc_output?: QaQcHseData["qaqc_output"];
  hse_output?: QaQcHseData["hse_output"];
  contract_output?: { risks: ContractRisk[] };
  claims_output?: ClaimsData;
  llm_metrics_output?: LlmMetrics;
  bim_output?: BimData;
  dossier_output?: DossierData;
  dispatch_output?: any; 
  field_output?: any; 
  blockchain_output?: any; 
  pitch_deck_output?: any; 
  ve_output?: any; 
  submittal_output?: any; 
  ipc_output?: any; // Matches IPCData from IpcPaymentStudio
  [key: string]: unknown;
}

export function useTenderAudit(tenderId: number, tenant: TenantContext) {
  const [status, setStatus] = useState<string>('idle');
  const [score, setScore] = useState<number | null>(null);
  const [records, setRecords] = useState<ComplianceRecord[]>([]);
  const [redTeamData, setRedTeamData] = useState<AuditMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    if (!tenderId || tenderId <= 0) {
      setStatus('idle');
      setScore(null);
      setRecords([]);
      setRedTeamData(null);
      setError(null);
      return;
    }
    try {
      const data = await fetchTenderStatus(tenderId, tenant);
      if (!data) return;
      setStatus(data.status);
      if (data.status === 'failed') {
        const err = (data.audit_metadata as { error?: { message?: string } } | undefined)?.error;
        setError(err?.message || 'فشل التدقيق / Audit failed');
        setScore(null);
        setRecords([]);
        setRedTeamData(null);
      } else {
        setError(null);
      }
      if (data.status === 'completed' || data.status === 'audited') {
        setScore(data.technical_score);
        setRecords((data.records as unknown as ComplianceRecord[]) || []);
        setRedTeamData((data.audit_metadata as AuditMetadata) || null);
      }
    } catch (e) {
      console.error(e);
    }
  }, [tenderId, tenant]);

  // Poll immediately on mount and whenever the tender id changes (new ingestion).
  useEffect(() => {
    pollStatus();
  }, [pollStatus]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (status === 'processing') {
      interval = setInterval(pollStatus, 3000);
    }
    return () => clearInterval(interval);
  }, [status, pollStatus]);

  const downloadReport = () => {
    window.location.href = `http://localhost:8000/api/v1/audits/${tenderId}/export`;
  };

  return { status, score, records, redTeamData, error, pollStatus, downloadReport };
}