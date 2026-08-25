'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Activity, Cpu, DollarSign, FileText, Radio, ShieldCheck, Loader2, Download, ArrowLeft,
} from 'lucide-react';
import { ComplianceBadge } from '../../components/ui/ComplianceBadge';

const SSE_BASE = 'http://localhost:8000';

const AGENTS = [
  'RFP Deconstructor', 'BOQ Parser', 'Methodology Auditor', 'P6 Schedule Auditor',
  'Standards Agent', 'Cross-Exam Agent', 'VE Optimizer', 'Contract Agent',
  'Bid Evaluator', 'Gatekeeper',
];

interface LlmSnapshot {
  total_tokens: number;
  total_cost_usd: number;
  active_model: string;
  models_distribution: Record<string, number>;
}

const COMPLIANCE_ROWS = [
  { clause: 'SBC-304 §5.2', req: "f'c >= exposure minimum", status: 'COMPLIANT' },
  { clause: 'SBC-304 §5.3', req: 'w/c within ceiling', status: 'COMPLIANT_WITH_DEVIATION' },
  { clause: 'SBC-304 §7.7', req: 'Minimum concrete cover', status: 'COMPLIANT' },
  { clause: 'SBC-304 Table 4.3.1', req: 'Exposure-class limits', status: 'NON_COMPLIANT' },
];

export default function MissionControlPage() {
  const [connected, setConnected] = useState(false);
  const [llm, setLlm] = useState<LlmSnapshot>({
    total_tokens: 0, total_cost_usd: 0, active_model: 'gpt-4-turbo', models_distribution: {},
  });
  const [runningAgents, setRunningAgents] = useState<Record<string, boolean>>({});

  // Live LLM gateway telemetry stream.
  useEffect(() => {
    const es = new EventSource(`${SSE_BASE}/api/v1/telemetry/llm-stream`);
    es.onopen = () => setConnected(true);
    es.onerror = () => { setConnected(false); };
    es.addEventListener('llm_snapshot', (ev) => {
      try { setLlm(JSON.parse((ev as MessageEvent).data)); } catch { /* noop */ }
    });
    es.addEventListener('llm_update', (ev) => {
      try { setLlm(JSON.parse((ev as MessageEvent).data)); } catch { /* noop */ }
    });
    return () => es.close();
  }, []);

  // Simulated agent-state drift (production binds the swarm SSE stream).
  useEffect(() => {
    const interval = setInterval(() => {
      setRunningAgents((prev) => {
        const next: Record<string, boolean> = {};
        AGENTS.forEach((a, i) => { next[a] = Math.random() > 0.4; });
        return { ...prev, ...next };
      });
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  const totalDistribution = Object.values(llm.models_distribution).reduce((s, v) => s + v, 0);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-slate-500 hover:text-teal-300 transition">
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-xl font-black tracking-tight flex items-center gap-2">
                <Activity className="h-5 w-5 text-teal-400" /> Mission Control
              </h1>
              <p className="text-xs text-slate-500">Live tender pipeline telemetry — agent swarm, token burn, compliance.</p>
            </div>
          </div>
          <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full border ${
            connected ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/15 text-amber-300 border-amber-500/40'
          }`}>
            <Radio className={`h-3 w-3 ${connected ? 'animate-pulse' : ''}`} />
            {connected ? 'SSE LIVE' : 'RECONNECTING'}
          </span>
        </div>

        {/* Swarm Status Grid */}
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
          <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4">Swarm Status Grid</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {AGENTS.map((agent) => {
              const running = runningAgents[agent] ?? false;
              return (
                <div key={agent} className={`rounded-xl border p-3 transition ${
                  running ? 'border-teal-500/40 bg-teal-500/5' : 'border-slate-800 bg-slate-950/40'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-400">{agent}</span>
                    {running ? (
                      <Loader2 className="h-3.5 w-3.5 text-teal-400 animate-spin" />
                    ) : (
                      <span className="h-2 w-2 rounded-full bg-slate-600" />
                    )}
                  </div>
                  <p className={`text-[9px] font-black uppercase tracking-wider mt-2 ${running ? 'text-teal-300' : 'text-slate-600'}`}>
                    {running ? 'PROCESSING' : 'STANDBY'}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Token + Cost Counter */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Total Tokens</span>
              <Cpu className="h-4 w-4 text-cyan-400" />
            </div>
            <p className="text-3xl font-black font-mono text-white">{llm.total_tokens.toLocaleString()}</p>
            <p className="text-xs text-slate-500 mt-1">Active model: <span className="font-mono text-cyan-300">{llm.active_model}</span></p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Est. API Cost</span>
              <DollarSign className="h-4 w-4 text-emerald-400" />
            </div>
            <p className="text-3xl font-black font-mono text-emerald-400">${llm.total_cost_usd.toFixed(4)}</p>
            <p className="text-xs text-slate-500 mt-1">Live accrual via llm-stream</p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Swarm Distribution</span>
              <Activity className="h-4 w-4 text-blue-400" />
            </div>
            <div className="space-y-1.5 mt-1">
              {Object.entries(llm.models_distribution).map(([model, tokens]) => {
                const pct = totalDistribution ? Math.round((tokens / totalDistribution) * 100) : 0;
                return (
                  <div key={model} className="flex items-center gap-2 text-xs">
                    <span className="w-32 font-mono text-slate-400">{model}</span>
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{ width: `${pct}%` }} />
                    </div>
                    <span className="w-10 text-right font-mono text-slate-500">{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Compliance + Certified PDF */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-teal-400" /> Structural &amp; Geotechnical Compliance Matrix
            </h2>
            <div className="space-y-2">
              {COMPLIANCE_ROWS.map((row) => (
                <div key={row.clause} className="flex items-center justify-between gap-3 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2.5">
                  <div className="min-w-0">
                    <p className="text-xs font-black font-mono text-teal-300">{row.clause}</p>
                    <p className="text-[10px] text-slate-500 truncate">{row.req}</p>
                  </div>
                  <ComplianceBadge status={row.status} />
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col">
            <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4 flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-400" /> Certified Proposal Dossier
            </h2>
            <div className="flex-1 rounded-xl border border-dashed border-slate-700 bg-slate-950/40 flex flex-col items-center justify-center p-8 text-center">
              <FileText className="h-10 w-10 text-slate-600 mb-3" />
              <p className="text-sm font-bold text-slate-300">Technical_Proposal_Certified.pdf</p>
              <p className="text-xs text-slate-600 mt-1">PAdES-LTV signed · SBC-304 clearance embedded · QR verified</p>
              <div className="flex gap-3 mt-5">
                <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/40 hover:bg-blue-500/25 transition">
                  <Download className="h-4 w-4" /> Download
                </button>
                <button className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-teal-500/15 text-teal-300 border border-teal-500/40 hover:bg-teal-500/25 transition">
                  View Embedded
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
