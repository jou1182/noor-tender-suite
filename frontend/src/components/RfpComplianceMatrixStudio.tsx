"use client";

import React, { useEffect, useMemo, useState } from 'react';
import {
  FileSearch, CheckCircle2, AlertTriangle, XCircle, Copy, Check, ChevronDown, Sparkles, ShieldAlert, Radio,
} from 'lucide-react';
import { ComplianceRecord } from './ComplianceMatrixTable';

export interface RfpComplianceRecord extends ComplianceRecord {
  proposal_section?: string;
  discrepancy?: string;
  remediation?: string;
}

type Verdict = 'Compliant' | 'Minor Deviation' | 'Critical Gap';
type FilterKey = 'All' | Verdict;

const STATUS_MAP: Record<string, Verdict> = {
  Compliant: 'Compliant', Pass: 'Compliant', COMPLIANT: 'Compliant',
  'Minor Deviation': 'Minor Deviation', Deviation: 'Minor Deviation', Gap: 'Minor Deviation', Partial: 'Minor Deviation', MINOR_DEVIATION: 'Minor Deviation',
  'Critical Gap': 'Critical Gap', Fail: 'Critical Gap', 'Non-Compliant': 'Critical Gap', CRITICAL_GAP: 'Critical Gap',
};

const VERDICT_CONFIG: Record<Verdict, { icon: React.ElementType; badge: string; ring: string; dot: string }> = {
  Compliant: { icon: CheckCircle2, badge: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40', ring: 'border-l-emerald-500/60', dot: 'bg-emerald-400' },
  'Minor Deviation': { icon: AlertTriangle, badge: 'bg-amber-500/15 text-amber-300 border-amber-500/40', ring: 'border-l-amber-500/60', dot: 'bg-amber-400' },
  'Critical Gap': { icon: XCircle, badge: 'bg-rose-500/15 text-rose-300 border-rose-500/40', ring: 'border-l-rose-500/60', dot: 'bg-rose-400' },
};

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
  HIGH: 'bg-orange-500/15 text-orange-300 border-orange-500/40',
  MEDIUM: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  LOW: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
};

function normalize(status: string): Verdict {
  return STATUS_MAP[status] || 'Deviation';
}

function generateRemediation(record: ComplianceRecord): string {
  const verdict = normalize(record.status);
  const gap = record.gap_analysis || 'No evidence provided';
  if (verdict === 'Compliant') {
    return `No action required — clause satisfied. Retain supporting evidence (${gap}) and reference ${record.clause_code} in the compliance register.`;
  }
  if (verdict === 'Minor Deviation') {
    return `Revise proposal section: ${gap}. Add corrective evidence against ${record.clause_code} and re-submit for re-evaluation.`;
  }
  return `BLOCKING — ${gap}. Insert a corrective clause addressing ${record.clause_code} into the proposal, attach the missing evidence, and re-certify before submission.`;
}

function ComplianceScoreRing({ score }: { score: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 90 ? '#34d399' : score >= 70 ? '#fbbf24' : '#fb7185';
  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={radius} fill="none" stroke="#1e293b" strokeWidth="10" />
        <circle cx="50" cy="50" r={radius} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset} style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-2xl font-black tracking-tight" style={{ color }}>{score}%</span>
        <span className="text-[8px] font-bold uppercase tracking-widest text-slate-500">Compliant</span>
      </div>
    </div>
  );
}

/** Maps the backend matrix payload to the studio's record shape. */
function matrixToRecords(payload: any): RfpComplianceRecord[] {
  if (!payload || !Array.isArray(payload.matrix)) return [];

  return payload.matrix.map((row: any, idx: number) => ({
    clause_code: row.clause_ref ?? row.clause_code ?? `RFP-C${idx + 1}`,
    requirement: row.clause_text ?? row.requirement ?? '',
    status: row.status ?? 'Compliant',
    severity: row.strictness === 'Mandatory' ? 'HIGH' : 'MEDIUM',
    gap_analysis: row.clause_text ?? '',
    proposal_section: row.matched_section ?? '—',
    discrepancy: row.clause_text ?? '',
    remediation: row.remediation ?? '',
  }));
}

const SSE_URL = 'http://localhost:8000/api/v1/telemetry/stream/compliance';

export const RfpComplianceMatrixStudio: React.FC<{ records: ComplianceRecord[]; tenderId?: number }> = ({ records, tenderId }) => {
  const [filter, setFilter] = useState<FilterKey>('All');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [copied, setCopied] = useState<number | null>(null);
  const [liveRecords, setLiveRecords] = useState<RfpComplianceRecord[] | null>(null);
  const [liveScore, setLiveScore] = useState<number | null>(null);
  const [streamState, setStreamState] = useState<'idle' | 'connecting' | 'live' | 'closed'>('idle');
  const [accepted, setAccepted] = useState<number | null>(null);
  const [proposalDraft, setProposalDraft] = useState<string[]>([]);

  // Bind to the SSE compliance stream — hydrates score + gap table in real time
  // without page reloads. The backend replays the latest matrix on connect.
  useEffect(() => {
    setStreamState('connecting');
    const eventSource = new EventSource(SSE_URL);

    eventSource.onopen = () => setStreamState('live');
    eventSource.addEventListener('rfp_compliance_update', (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data);
        const hydrated = matrixToRecords(payload);
        if (hydrated.length > 0) {
          setLiveRecords(hydrated);
        }
        if (typeof payload.compliance_score === 'number') {
          setLiveScore(payload.compliance_score);
        }
      } catch (e) {
        console.error('Invalid rfp_compliance_update payload', e);
      }
    });
    eventSource.onerror = () => {
      setStreamState('closed');
      eventSource.close();
    };

    return () => eventSource.close();
  }, []);

  // سجلات المنافسة النشطة من قاعدة البيانات — المصدر الأساسي (قبل SSE وdemo)
  const [tenderRecords, setTenderRecords] = useState<ComplianceRecord[] | null>(null);
  const [tenderTitle, setTenderTitle] = useState<string>('');

  useEffect(() => {
    if (!tenderId) return;
    let cancelled = false;
    (async () => {
      try {
        const { getDemoToken } = await import('../lib/api_client');
        const token = await getDemoToken({
          id: String(tenderId), name: '', project: '', phase: '', role: 'lead_architect',
        } as never);
        const res = await fetch(`http://localhost:8000/api/v1/audits/${tenderId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok || cancelled) return;
        const data = await res.json();
        if (cancelled) return;
        if (Array.isArray(data.records) && data.records.length > 0) {
          setTenderRecords(data.records as ComplianceRecord[]);
        } else {
          setTenderRecords([]); // المنافسة موجودة لكن بلا نتائج بعد — لا demo
        }
        if (data.title) setTenderTitle(String(data.title));
      } catch { /* تعمل بالسجلات الممررة كخصائص */ }
    })();
    return () => { cancelled = true; };
  }, [tenderId]);

  // أولوية المصادر: SSE الحي ← قاعدة بيانات المنافسة ← الخاصية الممررة
  const sourceRecords: RfpComplianceRecord[] =
    liveRecords ?? (tenderRecords as RfpComplianceRecord[] | null) ?? (records as RfpComplianceRecord[]);
  const rows: RfpComplianceRecord[] = useMemo(
    () => sourceRecords.map((r, idx) => {
      const rich = r as RfpComplianceRecord;
      return {
        ...r,
        proposal_section: rich.proposal_section ?? `Technical Proposal §${idx + 1}`,
        discrepancy: rich.discrepancy ?? rich.gap_analysis ?? 'No discrepancy recorded.',
        remediation: rich.remediation ?? generateRemediation(r),
      };
    }),
    [sourceRecords],
  );

  const counts: Record<Verdict, number> = useMemo(
    () => ({
      Compliant: rows.filter((r) => normalize(r.status) === 'Compliant').length,
      'Minor Deviation': rows.filter((r) => normalize(r.status) === 'Minor Deviation').length,
      'Critical Gap': rows.filter((r) => normalize(r.status) === 'Critical Gap').length,
    }),
    [rows],
  );

  const score = liveScore ?? (rows.length > 0 ? Math.round((counts.Compliant / rows.length) * 100) : 0);
  const filtered = filter === 'All' ? rows : rows.filter((r) => normalize(r.status) === filter);

  const fallbackCopy = (text: string) => {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch {
      /* clipboard unavailable */
    }
    document.body.removeChild(ta);
  };

  const copyToProposal = (text: string, idx: number) => {
    setCopied(idx);
    setTimeout(() => setCopied((c) => (c === idx ? null : c)), 3000);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  };

  // One-click remediation: accept the AI-generated clause and append it to the
  // master proposal draft (component-level state for this studio; the same
  // payload feeds the exported compliance register).
  const acceptRemediation = (text: string, idx: number) => {
    setAccepted(idx);
    setProposalDraft((draft) => (draft.includes(text) ? draft : [...draft, text]));
    setTimeout(() => setAccepted((a) => (a === idx ? null : a)), 3000);
  };

  const streamBadge = streamState === 'live' ? (
    <span className="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 rounded-full px-3 py-1.5">
      <Radio className="h-3 w-3 animate-pulse" /> Live SSE
    </span>
  ) : streamState === 'connecting' ? (
    <span className="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest bg-amber-500/15 text-amber-300 border border-amber-500/40 rounded-full px-3 py-1.5">
      Connecting…
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest bg-slate-500/15 text-slate-400 border border-slate-600 rounded-full px-3 py-1.5">
      Stream closed
    </span>
  );

  return (
    <div className="rounded-lg shadow-2xl border mt-8 mb-8 bg-slate-900 border-slate-700 animate-in fade-in duration-500 text-slate-100 font-sans overflow-hidden">
      <div className="p-5 border-b border-slate-700 bg-black/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-xl font-black flex items-center text-teal-400 tracking-wide">
            <FileSearch className="mr-3 shrink-0" size={26} /> RFP Compliance Studio
            {tenderTitle && (
              <span className="ml-3 text-xs font-bold text-slate-400 border border-slate-700 rounded-full px-3 py-1 truncate max-w-[220px]" title={tenderTitle}>
                {tenderTitle}
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 mt-1.5 ml-9">Clause-by-clause evaluation — RFP requirements vs technical proposal sections</p>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          {streamBadge}
          <ComplianceScoreRing score={score} />
          <div className="flex flex-col gap-1.5">
            {(['Compliant', 'Minor Deviation', 'Critical Gap'] as Verdict[]).map((v) => {
              const cfg = VERDICT_CONFIG[v];
              return (
                <span key={v} className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${cfg.dot}`} /> {v} · {counts[v]}
                </span>
              );
            })}
          </div>
        </div>
      </div>

      <div className="p-6">
        {proposalDraft.length > 0 && (
          <div className="mb-5 rounded-lg border border-blue-500/40 bg-blue-950/30 p-3">
            <p className="text-[10px] font-black uppercase tracking-widest text-blue-300 mb-2 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" /> Master Proposal Draft — accepted remediation clauses ({proposalDraft.length})
            </p>
            <ul className="space-y-1.5">
              {proposalDraft.map((line, i) => (
                <li key={i} className="text-xs font-mono text-slate-200 leading-relaxed flex items-start gap-2">
                  <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 mb-5">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mr-1">Filter:</span>
          {(['All', 'Compliant', 'Minor Deviation', 'Critical Gap'] as FilterKey[]).map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-full border transition ${
                filter === f ? 'bg-teal-500/15 text-teal-300 border-teal-500/40' : 'bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}>
              {f === 'All' ? `All (${rows.length})` : f}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <ShieldAlert className="h-10 w-10 text-slate-600 mb-3" />
            <p className="text-sm font-semibold text-slate-400">No clauses match this filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800">
              <thead className="bg-slate-950/60">
                <tr>
                  <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-widest w-28">Clause</th>
                  <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-widest">RFP Requirement</th>
                  <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-widest">Proposal Section</th>
                  <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-widest w-24">Severity</th>
                  <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-widest w-36">Status</th>
                  <th className="px-3 py-3 text-right text-[10px] font-black text-slate-500 uppercase tracking-widest w-10" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-900/40">
                {filtered.map((r, i) => {
                  const verdict = normalize(r.status);
                  const cfg = VERDICT_CONFIG[verdict];
                  const Icon = cfg.icon;
                  const sevStyle = SEVERITY_STYLES[r.severity?.toUpperCase()] || SEVERITY_STYLES.LOW;
                  const isOpen = expanded === i;
                  return (
                    <React.Fragment key={`${r.clause_code}-${i}`}>
                      <tr className={`border-l-2 ${cfg.ring} hover:bg-slate-800/40 transition cursor-pointer`} onClick={() => setExpanded(isOpen ? null : i)}>
                        <td className="whitespace-nowrap px-3 py-3 text-xs font-black text-teal-300 font-mono">{r.clause_code}</td>
                        <td className="px-3 py-3 text-sm text-slate-200">{r.requirement}</td>
                        <td className="whitespace-nowrap px-3 py-3 text-xs text-slate-400">{r.proposal_section}</td>
                        <td className="whitespace-nowrap px-3 py-3">
                          <span className={`inline-block text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${sevStyle}`}>{r.severity || 'LOW'}</span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-3">
                          <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border ${cfg.badge}`}>
                            <Icon className="h-3 w-3" /> {verdict}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-right">
                          <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                        </td>
                      </tr>
                      {isOpen && (
                        <tr className="bg-slate-950/60">
                          <td colSpan={6} className="px-6 py-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              <div>
                                <p className="text-[10px] font-black uppercase tracking-widest text-rose-400 mb-2 flex items-center gap-1.5">
                                  <XCircle className="h-3.5 w-3.5" /> Discrepancy Detail
                                </p>
                                <p className="text-sm text-slate-300 leading-relaxed">{r.discrepancy}</p>
                              </div>
                              <div className="rounded-lg border border-teal-500/30 bg-teal-950/20 p-3">
                                <p className="text-[10px] font-black uppercase tracking-widest text-teal-300 mb-2 flex items-center gap-1.5">
                                  <Sparkles className="h-3.5 w-3.5" /> AI Remediation Snippet
                                </p>
                                <p className="text-xs text-slate-200 leading-relaxed font-mono">{r.remediation}</p>
                                <div className="mt-3 flex flex-wrap gap-2">
                                  <button
                                    onClick={(e) => { e.stopPropagation(); acceptRemediation(r.remediation || '', i); }}
                                    className={`inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border transition ${
                                      accepted === i ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' : 'bg-blue-500/15 text-blue-300 border-blue-500/40 hover:bg-blue-500/25'
                                    }`}
                                  >
                                    {accepted === i ? <Check className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
                                    {accepted === i ? 'Accepted' : 'Accept into Proposal'}
                                  </button>
                                  <button
                                    onClick={(e) => { e.stopPropagation(); copyToProposal(r.remediation || '', i); }}
                                    className={`inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border transition ${
                                      copied === i ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' : 'bg-teal-500/15 text-teal-300 border-teal-500/40 hover:bg-teal-500/25'
                                    }`}
                                  >
                                    {copied === i ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                                    {copied === i ? 'Copied' : 'Copy'}
                                  </button>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
