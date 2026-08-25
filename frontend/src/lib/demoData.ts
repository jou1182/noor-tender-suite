import type { LlmMetrics } from '../components/LlmUsageCard';
import type { ComplianceRecord } from '../components/ComplianceMatrixTable';
import type { SubmittalData } from '../components/SubmittalReviewStudio';
import type { VEOpportunityCard, VESummary } from '../types/ve';
import type { ScheduleHealthData } from '../components/ScheduleHealthStudio';
import type { PitchDeckData, Simulation4DData } from '../components/Simulation4DStudio';
import type { QaQcHseData } from '../components/ItpHseStudio';
import type { ClaimsData } from '../components/ClaimsStudio';
import type { IPCData } from '../components/IpcPaymentStudio';
import type { FieldData } from '../components/SiteOperationsStudio';
import type { DossierData } from '../components/MasterExportStudio';
import type { BlockchainData } from '../components/BlockchainLedgerStudio';

export interface TenantContext {
  id: string;
  name: string;
  project: string;
  phase: string;
  role: string;
}

export const TENANTS: TenantContext[] = [
  { id: 'aramco', name: 'Saudi Aramco', project: 'NEOM Capital Works Package', phase: 'Bid Phase', role: 'Lead Architect' },
  { id: 'rosn', name: 'ROSHN Group', project: 'Riyadh District 3 Residential', phase: 'Tender Evaluation', role: 'Commercial Director' },
  { id: 'rsg', name: 'Red Sea Global', project: 'AMALA Marina Civil Works', phase: 'Pre-Qualification', role: 'Estimation Head' },
  { id: 'qiddiya', name: 'Qiddiya Investment Co.', project: 'Six Flags Infrastructure', phase: 'Tender Preparation', role: 'Technical Lead' },
];

export const demoSystemHealth = {
  status: 'Operational' as const,
  active_workflows: 142,
  avg_llm_latency_ms: 245,
  error_rate_pct: 0.02,
  recent_alerts: [
    { timestamp: '14:32:01', title: 'ETIMAD Compliance Blocker: Missing Guarantee', severity: 'CRITICAL' },
    { timestamp: '12:15:44', title: 'Qdrant Vector DB Latency Spike (>500ms)', severity: 'WARNING' },
    { timestamp: '09:04:11', title: 'Cross-Exam Agent completed adversarial review', severity: 'INFO' },
  ],
};

export const demoLlmMetrics: LlmMetrics = {
  total_tokens: 1425890,
  total_cost_usd: 21.38,
  primary_model: 'gpt-4-turbo',
  fallback_triggered: false,
  models_distribution: {
    'gpt-4-turbo': 850400,
    'claude-3-opus': 410290,
    'gemini-1.5-pro': 165200,
  },
};

export const demoSubmittalData: SubmittalData = {
  material_name: 'High-Performance Concrete Mix Design (C40) - Substructure',
  review_status: 'CODE_B',
  review_action: 'Approved as Noted',
  discrepancies_found: 1,
  parameters_evaluated: [
    { name: '28-Day Compressive Strength', required_value: 40, submitted_value: 42.5, operator: '>=', unit: 'MPa', passed: true },
    { name: 'Water/Cement Ratio', required_value: 0.4, submitted_value: 0.38, operator: '<=', unit: 'Ratio', passed: true },
    { name: 'Chloride Ion Penetrability', required_value: 1000, submitted_value: 1100, operator: '<=', unit: 'Coulombs', passed: false },
  ],
  technical_commentary: [
    'Approved with minor deviations. See discrepancies for required field adjustments.',
    'Chloride Ion Penetrability: Required <= 1000, but Submitted is 1100. (Apply penetrating sealer onsite)',
  ],
};

export const demoVeCards: VEOpportunityCard[] = [
  {
    boq_item: 'Raft Foundation',
    original_spec: 'C35 OPC',
    proposed_alternative: 'C35 GGBFS 50% (Slag-Blended Cement)',
    unit_delta_sar: -49.6,
    net_savings_sar: 59520,
    speed_index_gain_percent: 12.0,
    sbc_status: 'COMPLIANT',
    is_recommended: true,
    technical_justification:
      "Slag replacement lowers unit cost and heat of hydration while meeting SBC 304 strength (f'c 35 MPa) and durability (w/c 0.40) requirements.",
    sbc_304_references: ['SBC 304 Table 4.3.1', 'SBC 304 Sec 7.7', 'SBC 304 §5.3'],
    is_accepted: false,
  },
  {
    boq_item: 'Slab on Grade',
    original_spec: 'C35 OPC',
    proposed_alternative: 'Lean Concrete (Low-Cement Fill)',
    unit_delta_sar: -203.0,
    net_savings_sar: 0,
    speed_index_gain_percent: 0,
    sbc_status: 'BLOCKED',
    is_recommended: false,
    technical_justification:
      "NON-COMPLIANT with SBC 304: f'c 18.0 MPa below SBC 304 requirement: >= 25.0 MPa (ExposureClass S1); w/c 0.6 exceeds SBC 304 limit: <= 0.45 (ExposureClass S1); cover 30.0 mm below SBC 304 Sec 7.7 minimum: >= 75.0 mm (CAST_AGAINST_EARTH)",
    sbc_304_references: ['SBC 304 Table 4.3.1'],
    is_accepted: false,
  },
];

export const demoVeSummary: VESummary = {
  total_potential_savings_sar: 59520,
  net_schedule_acceleration_percent: 12.0,
  total_sbc_verified_proposals: 1,
  total_blocked: 1,
};

export const demoScheduleHealth: ScheduleHealthData = {
  dcma_results: {
    overall_status: 'FAILED',
    metrics: [
      { check: '1. Logic (Missing Links)', value_pct: 12.5, threshold: 5.0, passed: false, description: 'Unlinked activities disrupt network flow.' },
      { check: '2. Negative Lags', value_pct: 0.0, threshold: 0.0, passed: true, description: 'Negative lags distort critical path float.' },
      { check: '3. High Float (> 44 Days)', value_pct: 8.2, threshold: 5.0, passed: false, description: 'Excessive float indicates unstable sequence.' },
      { check: '4. Hard Constraints', value_pct: 1.0, threshold: 5.0, passed: true, description: 'Fixed dates override dynamic logic.' },
    ],
  },
  monte_carlo: {
    p50_days: 345.5,
    p80_days: 372.0,
    p90_days: 388.5,
    distribution_curve: [
      { duration: 320, probability: 5 },
      { duration: 330, probability: 15 },
      { duration: 340, probability: 45 },
      { duration: 350, probability: 80 },
      { duration: 360, probability: 55 },
      { duration: 370, probability: 25 },
      { duration: 380, probability: 10 },
      { duration: 390, probability: 2 },
    ],
  },
};

export const demoPitchDeck: PitchDeckData = {
  title: 'Master Proposal Pitch Deck & 4D Execution Plan',
  slides: [
    { type: 'EXECUTIVE_SUMMARY', content: 'Comprehensive end-to-end multi-agent orchestration completed.' },
    { type: '4D_DIGITAL_TWIN', simulation_data: {} },
    { type: 'DCMA_METRICS', score: 'VERIFIED' },
  ],
};

export const demoSimulation4D: Simulation4DData = {
  simulation_timestamp: new Date().toISOString(),
  total_elements: 3,
  element_states: {
    'IFC-FOUNDATION-01': { state: 'COMPLETED', color: '#10b981', progress: 100 },
    'IFC-COREWALL-02': { state: 'IN_PROGRESS', color: '#3b82f6', progress: 45 },
    'IFC-ROOFSKU-03': { state: 'PLANNED', color: '#94a3b8', progress: 0 },
  },
};

export const demoItpHse: QaQcHseData = {
  qaqc_output: {
    itp_register: [
      { activity: 'Structural Rebar Inspection', reference: 'SBC 304', frequency: 'Before every pour', checkpoint: 'Hold Point' },
      { activity: 'Fresh Concrete Slump & Temp', reference: 'ASTM C143', frequency: 'Every transit mixer', checkpoint: 'Witness Point' },
      { activity: 'Compressive Strength Testing', reference: 'ASTM C39', frequency: '7 & 28 Days', checkpoint: 'Hold Point' },
      { activity: 'Formation Compaction Test (FDT)', reference: 'ASTM D1556', frequency: 'Every layer (250mm)', checkpoint: 'Witness Point' },
    ],
  },
  hse_output: {
    hira_register: [
      {
        task: 'Deep Trench / Mass Excavation',
        hazard: 'Cave-in / Collapse / Asphyxiation',
        probability: 4,
        severity: 4,
        risk_score: 16,
        mitigation: 'Install engineered shoring system. Daily atmospheric testing. Confined space permit required.',
      },
      {
        task: 'High-Volume Concrete Pouring',
        hazard: 'Pump line failure / Chemical burns',
        probability: 3,
        severity: 3,
        risk_score: 9,
        mitigation: 'Mandatory PPE (alkali-resistant). Daily ultrasonic thickness checks on pump elbows.',
      },
    ],
  },
};

export const demoClaims: ClaimsData = {
  baseline_completion: '2027-12-31',
  impacted_completion: '2028-01-25',
  eot_days: 25,
  entitlement: {
    event_date: '2026-08-01',
    notice_date: '2026-08-15',
    days_elapsed: 14,
    is_time_barred: false,
    warning: 'Notice submitted successfully within the strict 28-day contractual window.',
  },
  prolongation_cost: 375000.0,
  draft_claim_letter:
    'NOTICE OF CLAIM PURSUANT TO FIDIC SUB-CLAUSE 20.1\n\nDear Engineer,\n\nWe hereby give formal notice of our claim for an Extension of Time (EoT) and additional payment resulting from the Engineer\'s Instruction dated 2026-08-01.\n\nOur Time Impact Analysis (TIA) demonstrates a direct critical path delay of 25 days, shifting the contractual completion date from 2027-12-31 to 2028-01-25.\n\nEstimated prolongation costs currently amount to SAR 375,000.00. Full particulars will follow within 42 days.',
};

export const demoIpc: IPCData = {
  contract_value: 15000000.0,
  cumulative_gross: 4650000.0,
  actual_retention: 465000.0,
  actual_recovery: 250000.0,
  liquidated_damages: 0.0,
  total_deductions: 915000.0,
  cumulative_net: 3735000.0,
  amount_due_pre_vat: 2135000.0,
  vat_amount: 320250.0,
  total_certified_payment: 2455250.0,
  advance_payment_balance: 1050000.0,
  retention_balance_to_cap: 285000.0,
};

export const demoFieldData: FieldData = {
  transcript_processed:
    'Observer detected significant honeycombing on column C4 at level 2 drop panel. Also noticed missing PPE on the rebar team.',
  vision_tags_processed: ['honeycombing', 'missing_ppe'],
  total_defects: 2,
  ncrs_issued: [
    {
      ncr_id: 'NCR-20260822-HONE',
      defect_type: 'Honeycombing',
      sbc_violation_code: 'SBC-304',
      violation_desc: 'Concrete Structural Integrity Failure',
      severity: 'CRITICAL',
      status: 'OPEN',
      required_action: 'Immediate site remediation and Engineer review mandated per SBC-304 guidelines.',
    },
    {
      ncr_id: 'NCR-20260822-MISS',
      defect_type: 'Missing Ppe',
      sbc_violation_code: 'SBC-HSE',
      violation_desc: 'Site Safety & Health Mandatory Equipment Regulations',
      severity: 'MODERATE',
      status: 'OPEN',
      required_action: 'Immediate site remediation and Engineer review mandated per SBC-HSE guidelines.',
    },
  ],
  timestamp: new Date().toISOString(),
};

export const demoDossier: DossierData = {
  dossier_status: 'SEALED',
  sections_compiled: ['Executive Summary', 'Technical Methodology', 'P6 Schedule', 'Commercial Offer', 'QA/QC & HSE Register', 'Compliance Matrix'],
  manifest: {
    timestamp: '2026-08-22T14:32:01Z',
    master_hash: 'sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08',
    signatures: {
      'Executive Summary': '0x7c1b2e3a4f5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f',
      'P6 Schedule': '0x1a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5',
      'Commercial Offer': '0x9f8e7d6c5b4a3928171615141312111098765432',
    },
  },
};

export const demoBlockchain: BlockchainData = {
  block_height: 2048,
  merkle_root: '0x6f8c9a2b4d5e7f0a1b2c3d4e5f60718293a4b5c6d',
  block_hash: '0x8d2f1a7c6b3e9a5f0c4d7e2b8a1f3c9d5e6b7a8c',
  previous_hash: '0x3a9d5f2c7b1e6a8c0d4f9b2e5a7c3f1d6b8a9e0c',
  ledger_integrity_verified: true,
  timestamp: Date.now(),
  transactions: [
    { event_type: 'TRIGGER_AUDIT', tender_id: 'TND-2026-001', action: 'Multi-agent swarm initiated', signed_by: 'lead_architect' },
    { event_type: 'REPORT_SEAL', tender_id: 'TND-2026-001', action: 'Master export dossier hashed & sealed', signed_by: 'arbitrator_agent' },
    { event_type: 'DISPATCH', tender_id: 'TND-2026-001', action: 'Submission dispatched to Etimad portal', signed_by: 'submission_agent' },
    { event_type: 'FIELD_NCR', tender_id: 'TND-2026-001', action: 'NCR-20260822-HONE registered on-chain', signed_by: 'field_gateway' },
  ],
};

export const demoComplianceRecords: ComplianceRecord[] = [
  {
    clause_code: 'SBC-304 §4.2',
    requirement: 'Minimum 28-day compressive strength of 40 MPa for substructure concrete.',
    status: 'Pass',
    severity: 'CRITICAL',
    gap_analysis: 'Contractor submittal: C40 mix design with 42.5 MPa average — fully compliant with approved TDS.',
  },
  {
    clause_code: 'SBC-304 §5.1',
    requirement: 'Maximum water/cement ratio of 0.40 for reinforced concrete elements.',
    status: 'Pass',
    severity: 'HIGH',
    gap_analysis: 'Submitted W/C ratio 0.38 — within the permissible envelope.',
  },
  {
    clause_code: 'SBC-304 §6.3',
    requirement: 'Chloride ion penetrability not to exceed 1,000 Coulombs (RCPT).',
    status: 'Fail',
    severity: 'CRITICAL',
    gap_analysis: 'Submitted RCPT result 1,100 Coulombs — exceeds threshold. Requires penetrating sealer or mix redesign.',
  },
  {
    clause_code: 'ITP-QAQC §A.1',
    requirement: 'Hold point inspection of structural rebar before every concrete pour.',
    status: 'Pass',
    severity: 'HIGH',
    gap_analysis: 'ITP register submitted with hold point at "Before every pour" — verified against SBC 304.',
  },
  {
    clause_code: 'ITP-QAQC §B.3',
    requirement: 'Compressive strength testing at 7 and 28 days per ASTM C39.',
    status: 'Gap',
    severity: 'MEDIUM',
    gap_analysis: 'ITP lists 7 & 28-day testing, but lab accreditation certificate (ISO 17025) not yet attached.',
  },
  {
    clause_code: 'HSE-HIRA §2.4',
    requirement: 'Engineered shoring and confined-space permit for deep trench excavation.',
    status: 'Pass',
    severity: 'CRITICAL',
    gap_analysis: 'HIRA register includes cave-in mitigation with engineered shoring and daily atmospheric testing.',
  },
  {
    clause_code: 'ETIMAD §7',
    requirement: 'Mandatory initial bank guarantee (2.5% of bid value) prior to submission.',
    status: 'Fail',
    severity: 'CRITICAL',
    gap_analysis: 'No bank guarantee letter found in the commercial package — submission blocker per Etimad.',
  },
  {
    clause_code: 'CLS-FIDIC §20.1',
    requirement: 'Notice of claim to be submitted within 28 days of the delaying event.',
    status: 'Gap',
    severity: 'MEDIUM',
    gap_analysis: 'Draft notice prepared (14 days elapsed), but formal transmittal to the Engineer is pending.',
  },
  {
    clause_code: 'BIM-IFC §3.1',
    requirement: 'IFC4 model with element-level quantities reconciled to BOQ within 5% tolerance.',
    status: 'Pass',
    severity: 'HIGH',
    gap_analysis: 'BIM takeoff variance 1.2% (steel) — within acceptable tolerance.',
  },
  {
    clause_code: 'COMM-CSI §31',
    requirement: 'Earthworks trade package to include compaction testing (FDT) per ASTM D1556.',
    status: 'Pass',
    severity: 'MEDIUM',
    gap_analysis: 'Package scope includes FDT every 250mm layer with witness point — compliant.',
  },
];