"use client";

import React, { useEffect, useState } from 'react';
import {
  Gauge, Radar, Layers, Activity, Loader2, Radio, ClipboardCheck, TrendingDown,
  CalendarClock, HardHat, Scale, Banknote, FileText, Link, Database, Zap, FileSearch,
} from 'lucide-react';

import { SystemHealthMonitor } from '../components/SystemHealthMonitor';
import { LlmUsageCard } from '../components/LlmUsageCard';
import { ExecutivePortfolioDashboard } from '../components/ExecutivePortfolioDashboard';
import { AgentFlowCanvas } from '../components/AgentFlowCanvas';
import { SubmittalReviewStudio } from '../components/SubmittalReviewStudio';
import { ValueEngineeringStudio } from '../components/ValueEngineeringStudio';
import { ScheduleHealthStudio } from '../components/ScheduleHealthStudio';
import { Simulation4DStudio } from '../components/Simulation4DStudio';
import { ItpHseStudio } from '../components/ItpHseStudio';
import { ClaimsStudio } from '../components/ClaimsStudio';
import { IpcPaymentStudio } from '../components/IpcPaymentStudio';
import { SiteOperationsStudio } from '../components/SiteOperationsStudio';
import { MasterExportStudio } from '../components/MasterExportStudio';
import { BlockchainLedgerStudio } from '../components/BlockchainLedgerStudio';
import { RfpComplianceMatrixStudio } from '../components/RfpComplianceMatrixStudio';
import { DashboardHeader } from '../components/DashboardHeader';
import { UploadTenderModal } from '../components/UploadTenderModal';
import { DocumentLibrary } from '../components/DocumentLibrary';
import { ProposalDraftingStudio } from '../components/ProposalDraftingStudio';
import { launchTenderSwarm } from '../lib/tenders_client';
import { fetchPlatformOverview } from '../lib/analytics_client';
import type { PlatformOverview } from '../lib/analytics_client';

import { useTenderAudit } from '../hooks/useTenderAudit';
import { AuditTriggerResult } from '../lib/api_client';

import type { QaQcHseData } from '../components/ItpHseStudio';
import type { PitchDeckData, Simulation4DData } from '../components/Simulation4DStudio';
import type { BlockchainData } from '../components/BlockchainLedgerStudio';
import type { LlmMetrics } from '../components/LlmUsageCard';
import type { VEOpportunityCard, VESummary } from '../types/ve';

import {
  demoSubmittalData, demoVeCards, demoVeSummary,
  demoScheduleHealth, demoPitchDeck, demoSimulation4D, demoItpHse, demoClaims,
  demoIpc, demoFieldData, demoDossier, demoBlockchain, demoComplianceRecords,
} from '../lib/demoData';
import type { TenantContext } from '../lib/demoData';

type StudioTab =
  | 'compliance' | 'submittal' | 'value_engineering' | 'schedule' | 'simulation' | 'itp_hse'
  | 'claims' | 'ipc' | 'site_ops' | 'master_export' | 'blockchain';

const STUDIO_TABS: { key: StudioTab; label: string; icon: React.ElementType }[] = [
  { key: 'compliance', label: 'RFP Compliance', icon: FileSearch },
  { key: 'submittal', label: 'Submittal Review', icon: ClipboardCheck },
  { key: 'value_engineering', label: 'Value Engineering', icon: TrendingDown },
  { key: 'schedule', label: 'Schedule Health', icon: CalendarClock },
  { key: 'simulation', label: '4D Simulation', icon: Layers },
  { key: 'itp_hse', label: 'ITP / HSE', icon: HardHat },
  { key: 'claims', label: 'Claims & EoT', icon: Scale },
  { key: 'ipc', label: 'IPC Payments', icon: Banknote },
  { key: 'site_ops', label: 'Site Operations', icon: Radio },
  { key: 'master_export', label: 'Master Export', icon: FileText },
  { key: 'blockchain', label: 'Blockchain Ledger', icon: Link },
];

export default function Dashboard() {
  const [tenderId, setTenderId] = useState<number>(1);
  const [swarmRun, setSwarmRun] = useState(0);
  const [tenant, setTenant] = useState<TenantContext>({ id: '1', name: 'Workspace', project: 'Loading…', phase: 'Draft', role: 'Lead Architect' });
  const [activeTab, setActiveTab] = useState<StudioTab>('compliance');
  const [uploadOpen, setUploadOpen] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [launchError, setLaunchError] = useState<string | null>(null);

  const { status, score, redTeamData, records: auditRecords } = useTenderAudit(tenderId, tenant);

  // لوحة القيادة الحية — تُحدّث مع كل تغيير في حالة التدقيق
  const [overview, setOverview] = useState<PlatformOverview | null>(null);
  useEffect(() => {
    fetchPlatformOverview().then(setOverview);
  }, [status, tenderId, swarmRun]);

  // مزامنة الهوية مع القائمة الديناميكية عند تغيّرها من الهيدر
  useEffect(() => {
    const idNum = Number(tenant.id);
    if (!Number.isNaN(idNum)) setTenderId(idNum);
  }, [tenant.id]);

  const handleLaunchSwarm = async () => {
    if (launching) return;
    setLaunching(true);
    setLaunchError(null);
    try {
      await launchTenderSwarm(tenderId);
      setSwarmRun((r) => r + 1);
    } catch (e) {
      setLaunchError(e instanceof Error ? e.message : 'تعذر إطلاق السرب.');
    } finally {
      setLaunching(false);
    }
  };

  const complianceRecords = auditRecords.length > 0 ? auditRecords : demoComplianceRecords;

  const itpHseData: QaQcHseData =
    redTeamData?.qaqc_output || redTeamData?.hse_output
      ? { qaqc_output: redTeamData?.qaqc_output, hse_output: redTeamData?.hse_output }
      : demoItpHse;

  const pitchData: PitchDeckData = (redTeamData?.pitch_deck_output as PitchDeckData) ?? demoPitchDeck;
  const simulationData: Simulation4DData =
    (redTeamData?.pitch_deck_output?.slides?.find((s: { type: string }) => s.type === '4D_DIGITAL_TWIN')?.simulation_data as Simulation4DData) ??
    demoSimulation4D;

  const blockchainData: BlockchainData = (redTeamData?.blockchain_output as BlockchainData) ?? demoBlockchain;

  const handleAuditSuccess = (result: AuditTriggerResult) => {
    setTenderId(result.tender_id);
    setSwarmRun((r) => r + 1);
  };

  const renderStudio = () => {
    switch (activeTab) {
      case 'compliance':
        return <RfpComplianceMatrixStudio records={complianceRecords} tenderId={tenderId} />;
      case 'submittal':
        return <SubmittalReviewStudio data={redTeamData?.submittal_output ?? demoSubmittalData} />;
      case 'value_engineering':
        return <ValueEngineeringStudio
          cards={(redTeamData?.ve_matrix as VEOpportunityCard[] | undefined) ?? demoVeCards}
          summary={(redTeamData?.ve_summary as VESummary | undefined) ?? demoVeSummary}
        />;
      case 'schedule':
        return <ScheduleHealthStudio data={redTeamData?.p6_output ?? demoScheduleHealth} />;
      case 'simulation':
        return <Simulation4DStudio pitchData={pitchData} simulationData={simulationData} />;
      case 'itp_hse':
        return <ItpHseStudio data={itpHseData} />;
      case 'claims':
        return <ClaimsStudio data={redTeamData?.claims_output ?? demoClaims} />;
      case 'ipc':
        return <IpcPaymentStudio data={redTeamData?.ipc_output ?? demoIpc} />;
      case 'site_ops':
        return <SiteOperationsStudio data={redTeamData?.field_output ?? demoFieldData} />;
      case 'master_export':
        return <MasterExportStudio data={redTeamData?.dossier_output ?? demoDossier} />;
      case 'blockchain':
        return <BlockchainLedgerStudio data={blockchainData} />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen relative bg-(--surface-page)">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-80 bg-[radial-gradient(60%_100%_at_50%_0%,oklch(70%_0.14_185/0.10),transparent_70%),radial-gradient(45%_90%_at_85%_10%,oklch(60%_0.15_250/0.08),transparent_70%)]"
      />
      <DashboardHeader tenant={tenant} onTenantChange={setTenant} onUploadClick={() => setUploadOpen(true)} />

      <UploadTenderModal
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        tenant={tenant}
        onSuccess={handleAuditSuccess}
      />

      <main className="max-w-[1400px] mx-auto px-4 md:px-6 py-6 space-y-8">
        {status === 'processing' && (
          <div className="flex items-center gap-3 bg-blue-50 border border-blue-200 text-blue-800 rounded-xl px-4 py-3">
            <Loader2 className="h-5 w-5 animate-spin shrink-0" />
            <span className="text-sm font-semibold">
              Multi-agent swarm auditing Tender #{tenderId} — watch the live swarm canvas below for streaming telemetry.
            </span>
          </div>
        )}
        {status === 'completed' && score !== null && (
          <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl px-4 py-3">
            <Activity className="h-5 w-5 shrink-0" />
            <span className="text-sm font-semibold">
              Audit complete — technical compliance score: <span className="font-black">{score}/100</span>. Studio workspaces below now reflect live agent output.
            </span>
          </div>
        )}

        <section className="space-y-4">
          <DocumentLibrary tenderId={tenderId} />
        </section>

        <section className="space-y-4">
          <ProposalDraftingStudio tenderId={tenderId} />
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center shrink-0">
              <Gauge className="h-4 w-4 text-white" />
            </span>
            <div>
              <h2 className="text-lg font-black text-slate-900 leading-tight">Command Center</h2>
              <p className="text-xs text-slate-500">Portfolio analytics, cluster telemetry &amp; LLM gateway economics</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 items-stretch">
            <ExecutivePortfolioDashboard overview={overview} />
            <SystemHealthMonitor overview={overview} />
            {/* بطاقة LLM تظهر فقط عند توفر قياسات حقيقية من آخر سرب — لا demo */}
            {(() => {
              const llm = redTeamData?.llm_metrics_output as LlmMetrics | undefined;
              return llm ? <LlmUsageCard data={llm} /> : null;
            })()}
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center shrink-0">
                <Radar className="h-4 w-4 text-white" />
              </span>
              <div>
                <h2 className="text-lg font-black text-slate-900 leading-tight">Multi-Agent Swarm Orchestration</h2>
                <p className="text-xs text-slate-500">LangGraph agent pipeline — click any node for agent detail</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {launchError && (
                <span className="max-w-xs truncate text-[11px] font-bold text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-3 py-1.5" title={launchError}>
                  {launchError}
                </span>
              )}
              <button
                onClick={handleLaunchSwarm}
                disabled={launching || status === 'processing'}
                title="يطلق سرب الوكلاء العشرة على المنافسة الحالية (يتطلب RFP + جدول زمني مرفوعين)"
                className={`flex items-center gap-2 text-[11px] font-black uppercase tracking-widest rounded-full px-4 py-2 border transition ${
                  status === 'processing'
                    ? 'bg-cyan-50 text-cyan-700 border-cyan-300 cursor-wait'
                    : 'bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow hover:from-teal-400 hover:to-blue-500 disabled:opacity-50'
                }`}
              >
                {status === 'processing' ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Swarm Running…</>
                ) : launching ? (
                  <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Launching…</>
                ) : (
                  <><Zap className="h-3.5 w-3.5" /> انطلق أيها الوكلاء</>
                )}
              </button>
              <span className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest bg-emerald-100 text-emerald-700 border border-emerald-300 rounded-full px-3 py-1.5">
                <Radio className="h-3 w-3 animate-pulse" /> Live SSE Telemetry
              </span>
            </div>
          </div>
          <div className="bg-slate-900 rounded-xl border border-slate-700 shadow-sm p-4">
            <AgentFlowCanvas key={swarmRun} tenderId={tenderId} />
          </div>
        </section>

        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center shrink-0">
              <Layers className="h-4 w-4 text-white" />
            </span>
            <div>
              <h2 className="text-lg font-black text-slate-900 leading-tight">Studio Workspaces</h2>
              <p className="text-xs text-slate-500">Agent-driven engineering, commercial &amp; field operations studios</p>
            </div>
          </div>

          <div className="bg-slate-800 rounded-xl shadow-sm overflow-hidden">
            <div className="flex overflow-x-auto border-b border-slate-700 bg-slate-900/60">
              {STUDIO_TABS.map((tab) => {
                const Icon = tab.icon;
                const active = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-2 px-4 py-3 text-xs font-bold whitespace-nowrap transition border-b-2 ${
                      active
                        ? 'text-white bg-gradient-to-r from-teal-500/20 to-blue-600/20 border-teal-400'
                        : 'text-slate-400 hover:text-white hover:bg-slate-700/40 border-transparent'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                  </button>
                );
              })}
            </div>
            <div className="-mt-8 -mb-8">{renderStudio()}</div>
          </div>
        </section>

        <footer className="flex flex-col md:flex-row items-center justify-between gap-2 pt-2 pb-6 text-[10px] text-slate-500 border-t border-teal-500/15">
          <span className="flex items-center gap-1.5 font-bold uppercase tracking-widest">
            <Zap className="h-3 w-3 text-teal-500" /> ConTech AI Platform · Multi-Agent Tender Intelligence
          </span>
          <span className="flex items-center gap-1.5">
            <Database className="h-3 w-3 text-blue-500" /> PostgreSQL · Qdrant · Redis · LangGraph — all systems operational
          </span>
        </footer>
      </main>
    </div>
  );
}