'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import {
  FolderKanban, Wallet, TrendingDown, ShieldCheck, Search, ChevronRight, Clock, Plus,
} from 'lucide-react';
import {
  PortfolioMetrics, ProjectClient, ProjectStatus, ProjectSummary,
} from '../../types/dashboard';

const METRICS: PortfolioMetrics = {
  total_active_tenders: 12,
  total_evaluated_value_sar: 1_284_500_000,
  net_ve_opportunities_sar: 42_750_000,
  overall_sbc_compliance_rate: 78.4,
};

const PROJECTS: ProjectSummary[] = [
  {
    id: 'a1f2c3d4', name: 'NEOM Capital Works Package', client: 'Saudi Aramco',
    tender_reference: 'RFQ-2026-0114', status: 'auditing', submission_due: '2026-09-30',
    technical_score: 82.5, evaluated_value_sar: 425_000_000, ve_opportunities_sar: 18_200_000,
    sbc_compliance_rate: 91.0, updated_at: '2026-08-22T10:00:00Z',
  },
  {
    id: 'b2e3d4e5', name: 'Riyadh District 3 Residential', client: 'ROSHN',
    tender_reference: 'TEN-2026-0871', status: 'ready_for_submission', submission_due: '2026-09-12',
    technical_score: 91.0, evaluated_value_sar: 312_000_000, ve_opportunities_sar: 9_850_000,
    sbc_compliance_rate: 96.2, updated_at: '2026-08-21T15:30:00Z',
  },
  {
    id: 'c3f4e5f6', name: 'Highway Corridor 10 Rehabilitation', client: 'Ministry of Transport',
    tender_reference: 'MOT-2026-0032', status: 'draft', submission_due: '2026-10-18',
    technical_score: null, evaluated_value_sar: 218_000_000, ve_opportunities_sar: 6_400_000,
    sbc_compliance_rate: null, updated_at: '2026-08-20T09:15:00Z',
  },
  {
    id: 'd4e5f6a7', name: 'Six Flags Infrastructure Works', client: 'Qiddiya',
    tender_reference: 'QID-2026-0550', status: 'auditing', submission_due: '2026-09-05',
    technical_score: 67.3, evaluated_value_sar: 198_500_000, ve_opportunities_sar: 4_100_000,
    sbc_compliance_rate: 63.0, updated_at: '2026-08-22T08:45:00Z',
  },
  {
    id: 'e5f6a7b8', name: 'AMALA Marina Civil Works', client: 'Red Sea Global',
    tender_reference: 'RSG-2026-0219', status: 'draft', submission_due: '2026-11-02',
    technical_score: null, evaluated_value_sar: 131_000_000, ve_opportunities_sar: 4_200_000,
    sbc_compliance_rate: null, updated_at: '2026-08-19T12:00:00Z',
  },
];

const CLIENTS: (ProjectClient | 'All')[] = ['All', 'ROSHN', 'Ministry of Transport', 'Qiddiya', 'Saudi Aramco', 'Red Sea Global'];
const STATUSES: (ProjectStatus | 'All')[] = ['All', 'draft', 'auditing', 'ready_for_submission'];

const STATUS_STYLE: Record<ProjectStatus, string> = {
  draft: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
  auditing: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  ready_for_submission: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  submitted: 'bg-blue-500/15 text-blue-300 border-blue-500/40',
};

const STATUS_LABEL: Record<ProjectStatus, string> = {
  draft: 'Draft',
  auditing: 'Auditing',
  ready_for_submission: 'Ready for Submission',
  submitted: 'Submitted',
};

const sar = (n: number) =>
  new Intl.NumberFormat('en-SA', { style: 'currency', currency: 'SAR', maximumFractionDigits: 0 }).format(n);

function daysUntil(due: string): number {
  const diff = new Date(due).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / 86_400_000));
}

export default function DashboardPage() {
  const [clientFilter, setClientFilter] = useState<ProjectClient | 'All'>('All');
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'All'>('All');
  const [query, setQuery] = useState('');

  const filtered = useMemo(
    () =>
      PROJECTS.filter((p) => {
        if (clientFilter !== 'All' && p.client !== clientFilter) return false;
        if (statusFilter !== 'All' && p.status !== statusFilter) return false;
        if (query && !`${p.name} ${p.tender_reference}`.toLowerCase().includes(query.toLowerCase())) return false;
        return true;
      }),
    [clientFilter, statusFilter, query],
  );

  return (
    <div className="space-y-6">
      {/* Portfolio Overview Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
            <FolderKanban className="h-6 w-6 text-teal-400" /> Project Portfolio
          </h1>
          <p className="text-sm text-slate-500 mt-1">Active tender packages, evaluated value and SBC compliance posture.</p>
        </div>
        <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2.5 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white hover:opacity-90 transition">
          <Plus className="h-4 w-4" /> New Tender
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Total Active Tenders</span>
            <FolderKanban className="h-4 w-4 text-teal-400" />
          </div>
          <p className="text-3xl font-black text-white font-mono">{METRICS.total_active_tenders}</p>
          <p className="text-xs text-slate-500 mt-1">Across 5 client workspaces</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Total Evaluated Value</span>
            <Wallet className="h-4 w-4 text-blue-400" />
          </div>
          <p className="text-3xl font-black text-white font-mono">{sar(METRICS.total_evaluated_value_sar)}</p>
          <p className="text-xs text-slate-500 mt-1">Live portfolio valuation</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Net VE Opportunities</span>
            <TrendingDown className="h-4 w-4 text-emerald-400" />
          </div>
          <p className="text-3xl font-black text-emerald-400 font-mono">{sar(METRICS.net_ve_opportunities_sar)}</p>
          <p className="text-xs text-slate-500 mt-1">SBC-verified savings identified</p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Overall SBC Compliance</span>
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-black text-cyan-400 font-mono">{METRICS.overall_sbc_compliance_rate}%</p>
          <p className="text-xs text-slate-500 mt-1">Weighted across active tenders</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-900 border border-slate-800 rounded-xl p-4">
        <div className="relative flex-1 min-w-56">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search project or tender reference…"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-teal-500/50"
          />
        </div>
        <select
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value as ProjectClient | 'All')}
          className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500/50"
        >
          {CLIENTS.map((c) => (
            <option key={c} value={c}>{c === 'All' ? 'All Clients' : c}</option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as ProjectStatus | 'All')}
          className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500/50"
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s === 'All' ? 'All Statuses' : STATUS_LABEL[s as ProjectStatus]}</option>
          ))}
        </select>
      </div>

      {/* Projects Data-Grid */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[1.6fr_1fr_1fr_0.9fr_0.9fr_1fr_0.9fr_0.6fr] gap-3 px-5 py-3 bg-slate-950/60 border-b border-slate-800 text-[10px] font-black uppercase tracking-widest text-slate-500">
          <span>Project</span>
          <span>Client</span>
          <span>Status</span>
          <span>Score</span>
          <span>Evaluated Value</span>
          <span>VE Opportunity</span>
          <span>Deadline</span>
          <span />
        </div>
        {filtered.map((p) => (
          <Link
            key={p.id}
            href={`/dashboard/projects/${p.id}/workspace`}
            className="grid grid-cols-[1.6fr_1fr_1fr_0.9fr_0.9fr_1fr_0.9fr_0.6fr] gap-3 items-center px-5 py-4 border-b border-slate-800/60 hover:bg-slate-800/40 transition"
          >
            <div className="min-w-0">
              <p className="text-sm font-bold text-slate-100 truncate">{p.name}</p>
              <p className="text-[10px] font-mono text-slate-500">{p.tender_reference}</p>
            </div>
            <span className="text-xs font-semibold text-slate-300">{p.client}</span>
            <span className={`inline-flex w-max items-center text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border ${STATUS_STYLE[p.status]}`}>
              {STATUS_LABEL[p.status]}
            </span>
            <span className="font-mono text-sm font-black text-slate-200">
              {p.technical_score !== null ? `${p.technical_score}%` : '—'}
            </span>
            <span className="font-mono text-xs text-slate-400">{sar(p.evaluated_value_sar)}</span>
            <span className="font-mono text-xs text-emerald-400">{sar(p.ve_opportunities_sar)}</span>
            <span className="flex items-center gap-1.5 text-xs text-slate-400">
              <Clock className="h-3.5 w-3.5 text-amber-400" />
              {daysUntil(p.submission_due)}d
            </span>
            <ChevronRight className="h-4 w-4 text-slate-600" />
          </Link>
        ))}
        {filtered.length === 0 && (
          <div className="py-14 text-center text-sm text-slate-500">No projects match the current filters.</div>
        )}
      </div>
    </div>
  );
}
