'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft, FileSearch, ShieldCheck, Lightbulb, FileText, UploadCloud,
  Building2, Hash, CalendarClock, Gauge, Download, Sparkles,
} from 'lucide-react';

import { DocumentDropzone } from '../../../../../components/DocumentDropzone';
import { ComplianceMatrixView } from '../../../../../components/ComplianceMatrixView';
import { ValueEngineeringStudio } from '../../../../../components/ValueEngineeringStudio';
import { LiveAgentTerminal } from '../../../../../components/LiveAgentTerminal';
import { useTenderStream } from '../../../../../hooks/useTenderStream';
import { VEOpportunityCard, VESummary } from '../../../../../types/ve';
import { ProjectSummary } from '../../../../../types/dashboard';

const DEMO_VE_CARDS: VEOpportunityCard[] = [
  {
    boq_item: 'Raft Foundation C35', original_spec: 'C35 OPC', proposed_alternative: 'C35 GGBFS 50% (Slag-Blended Cement)',
    unit_delta_sar: -49.6, net_savings_sar: 59_520, speed_index_gain_percent: 12.0,
    sbc_status: 'COMPLIANT', is_recommended: true,
    technical_justification: 'Slag replacement lowers unit cost and heat of hydration while meeting SBC 304 strength and durability requirements.',
    sbc_304_references: ['SBC 304 Table 4.3.1', 'SBC 304 Sec 7.7', 'SBC 304 §5.3'], is_accepted: false,
  },
  {
    boq_item: 'Grade 60 Steel Rebar', original_spec: 'Grade 60 Rebar', proposed_alternative: 'High-Yield Grade 80 Rebar',
    unit_delta_sar: -240.0, net_savings_sar: 2_040_000, speed_index_gain_percent: 8.5,
    sbc_status: 'COMPLIANT', is_recommended: true,
    technical_justification: 'Higher yield strength reduces tonnage and accelerates steel fixing duration.',
    sbc_304_references: ['SBC 304 §3.5.3', 'SBC 304 §6.1'], is_accepted: false,
  },
  {
    boq_item: 'Slab on Grade Lean Fill', original_spec: 'C35 OPC', proposed_alternative: 'Lean Concrete (Low-Cement Fill)',
    unit_delta_sar: -203.0, net_savings_sar: 0, speed_index_gain_percent: 0,
    sbc_status: 'BLOCKED', is_recommended: false,
    technical_justification: 'NON-COMPLIANT with SBC 304: f\'c 18 MPa below minimum; w/c 0.60 exceeds ceiling.',
    sbc_304_references: ['SBC 304 Table 4.3.1'], is_accepted: false,
  },
];

const DEMO_VE_SUMMARY: VESummary = {
  total_potential_savings_sar: 2_099_520,
  net_schedule_acceleration_percent: 10.25,
  total_sbc_verified_proposals: 2,
  total_blocked: 1,
};

const DEMO_METHOD_STATEMENTS = [
  { item: 'Raft Foundation C35', text: '1. Surface preparation. 2. Formwork installation. 3. Steel reinforcement placement. 4. Pouring and vibration. 5. Curing for 7 days. Compliant with SBC 304 severe exposure.', productivity: '40 m³/day' },
  { item: 'Grade 60 Steel Rebar', text: '1. Cutting/bending schedule. 2. Laps per SBC 304 §6.1. 3. Fixing at 200mm centres. 4. Cover spacers at 75mm for cast-against-earth.', productivity: '3.2 t/day' },
];

const DEMO_RISK_REGISTER = [
  { id: 'TEV-RISK-1', category: 'Structural & Code Compliance', severity: 'CRITICAL', mitigation: 'Re-certify S4 exposure mix before submission.' },
  { id: 'TEV-RISK-2', category: 'Material Specification Match', severity: 'MEDIUM', mitigation: 'Reduce w/c to 0.40 with admixture for S2 sections.' },
];

type WorkspaceTab = 'ingestion' | 'audit' | 've' | 'proposal';

const TABS: { key: WorkspaceTab; label: string; icon: React.ElementType }[] = [
  { key: 'ingestion', label: 'Document Ingestion', icon: UploadCloud },
  { key: 'audit', label: 'SBC-304 & Technical Audit', icon: ShieldCheck },
  { key: 've', label: 'Value Engineering Studio', icon: Lightbulb },
  { key: 'proposal', label: 'Proposal Assembly', icon: FileText },
];

export default function ProjectWorkspacePage() {
  const params = useParams<{ id: string }>();
  const projectId = params?.id ?? 'unknown';
  const [tab, setTab] = useState<WorkspaceTab>('ingestion');

  const { logs, connected } = useTenderStream(projectId);

  const project: ProjectSummary = {
    id: projectId,
    name: 'NEOM Capital Works Package',
    client: 'Saudi Aramco',
    tender_reference: 'RFQ-2026-0114',
    status: 'auditing',
    submission_due: '2026-09-30',
    technical_score: 82.5,
    evaluated_value_sar: 425_000_000,
    ve_opportunities_sar: 18_200_000,
    sbc_compliance_rate: 91.0,
    updated_at: new Date().toISOString(),
  };

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-teal-300 transition">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Portfolio
      </Link>

      {/* Top Workspace Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-teal-400 mb-2">
            <Building2 className="h-3.5 w-3.5" /> {project.client}
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white truncate">{project.name}</h1>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 mt-2 text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><Hash className="h-3.5 w-3.5 text-slate-500" /> {project.tender_reference}</span>
            <span className="flex items-center gap-1.5"><CalendarClock className="h-3.5 w-3.5 text-amber-400" /> Due {project.submission_due}</span>
            <span className="flex items-center gap-1.5"><Gauge className="h-3.5 w-3.5 text-teal-400" /> {project.sbc_compliance_rate}% SBC</span>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="text-right">
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Technical Score</p>
            <p className={`text-3xl font-black font-mono ${(project.technical_score ?? 0) >= 70 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {project.technical_score ?? '—'}%
            </p>
          </div>
          <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2.5 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white hover:opacity-90 transition">
            <FileSearch className="h-4 w-4" /> Run Audit
          </button>
        </div>
      </div>

      {/* Live agent stream */}
      <LiveAgentTerminal logs={logs} connected={connected} />

      {/* Tabbed Interface */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="flex overflow-x-auto border-b border-slate-800 bg-slate-950/60">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-bold whitespace-nowrap transition border-b-2 ${
                  active ? 'text-white bg-gradient-to-r from-teal-500/20 to-blue-600/20 border-teal-400' : 'text-slate-400 hover:text-white hover:bg-slate-800/40 border-transparent'
                }`}
              >
                <Icon className="h-4 w-4" /> {t.label}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {tab === 'ingestion' && <DocumentDropzone />}
          {tab === 'audit' && <ComplianceMatrixView />}
          {tab === 've' && <ValueEngineeringStudio cards={DEMO_VE_CARDS} summary={DEMO_VE_SUMMARY} />}
          {tab === 'proposal' && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {DEMO_METHOD_STATEMENTS.map((m) => (
                  <div key={m.item} className="bg-slate-950/40 border border-slate-800 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-bold text-slate-200">{m.item}</p>
                      <span className="text-[10px] font-mono font-black text-teal-400 bg-teal-500/10 border border-teal-500/30 px-2 py-0.5 rounded-full">{m.productivity}</span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed font-mono">{m.text}</p>
                  </div>
                ))}
              </div>

              <div className="bg-slate-950/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/60 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-rose-300">
                  <FileText className="h-3.5 w-3.5" /> Risk Register ({DEMO_RISK_REGISTER.length})
                </div>
                <div className="divide-y divide-slate-800">
                  {DEMO_RISK_REGISTER.map((r) => (
                    <div key={r.id} className="flex items-start gap-3 px-4 py-3">
                      <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border shrink-0 ${
                        r.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-300 border-rose-500/40' : 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                      }`}>{r.severity}</span>
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-slate-200">{r.category}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{r.mitigation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2.5 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/25 transition">
                  <Sparkles className="h-4 w-4" /> Generate Proposal Draft
                </button>
                <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2.5 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/40 hover:bg-blue-500/25 transition">
                  <Download className="h-4 w-4" /> Export Submission Package
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
