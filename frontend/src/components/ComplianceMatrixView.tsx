'use client';

import React, { useMemo, useState } from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { ComplianceVerdict } from '../types/dashboard';

interface ComplianceMatrixViewProps {
  verdicts?: ComplianceVerdict[];
  loading?: boolean;
}

const DEMO_VERDICTS: ComplianceVerdict[] = [
  {
    clause_code: 'SBC-304 §5.2', requirement: "Concrete compressive strength f'c >= design minimum",
    status: 'COMPLIANT', severity: 'LOW', gap_analysis: 'C35 mix verified at 42.5 MPa 28-day strength.', sbc_section: '5.2',
  },
  {
    clause_code: 'SBC-304 §5.3', requirement: 'Water/cement ratio within exposure ceiling',
    status: 'COMPLIANT_WITH_DEVIATION', severity: 'MEDIUM', gap_analysis: 'w/c 0.41 vs 0.40 ceiling for S2 — apply admixture reduction.', sbc_section: '5.3',
  },
  {
    clause_code: 'SBC-304 §7.7', requirement: 'Minimum concrete cover per placement context',
    status: 'COMPLIANT', severity: 'LOW', gap_analysis: 'Cover 75mm for cast-against-earth members verified.', sbc_section: '7.7',
  },
  {
    clause_code: 'SBC-304 Table 4.3.1', requirement: 'Exposure-class concrete limits',
    status: 'NON_COMPLIANT', severity: 'CRITICAL', gap_analysis: 'S4 exposure section uses S1 mix — re-certify design mix.', sbc_section: '4.3.1',
  },
  {
    clause_code: 'SBC-304 §3.5.3', requirement: 'Rebar yield strength within standard grades',
    status: 'COMPLIANT', severity: 'LOW', gap_analysis: 'Grade 60 (fy 420 MPa) confirmed.', sbc_section: '3.5.3',
  },
];

const BADGE: Record<ComplianceVerdict['status'], { icon: React.ElementType; cls: string; label: string }> = {
  COMPLIANT: { icon: CheckCircle2, cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40', label: 'Compliant' },
  COMPLIANT_WITH_DEVIATION: { icon: AlertTriangle, cls: 'bg-amber-500/15 text-amber-300 border-amber-500/40', label: 'Deviation' },
  NON_COMPLIANT: { icon: XCircle, cls: 'bg-rose-500/15 text-rose-300 border-rose-500/40', label: 'Non-Compliant' },
};

export const ComplianceMatrixView: React.FC<ComplianceMatrixViewProps> = ({ verdicts, loading = false }) => {
  const [filter, setFilter] = useState<ComplianceVerdict['status'] | 'All'>('All');
  const rows = verdicts ?? DEMO_VERDICTS;

  const counts = useMemo(
    () => ({
      COMPLIANT: rows.filter((r) => r.status === 'COMPLIANT').length,
      COMPLIANT_WITH_DEVIATION: rows.filter((r) => r.status === 'COMPLIANT_WITH_DEVIATION').length,
      NON_COMPLIANT: rows.filter((r) => r.status === 'NON_COMPLIANT').length,
    }),
    [rows],
  );

  const filtered = filter === 'All' ? rows : rows.filter((r) => r.status === filter);
  const rate = rows.length ? Math.round((counts.COMPLIANT / rows.length) * 100) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
          <ShieldCheck className="h-4 w-4 text-teal-400" />
          SBC-304 &amp; Technical Audit — {rate}% compliant
        </div>
        <div className="flex gap-2">
          {(['All', 'COMPLIANT', 'COMPLIANT_WITH_DEVIATION', 'NON_COMPLIANT'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded-full border transition ${
                filter === f ? 'bg-teal-500/15 text-teal-300 border-teal-500/40' : 'bg-slate-800/60 text-slate-400 border-slate-700 hover:text-slate-200'
              }`}
            >
              {f === 'All' ? `All (${rows.length})` : f.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-3">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-14 rounded-lg bg-slate-800" />
          ))}
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950/60 text-[10px] font-black uppercase tracking-widest text-slate-500">
                <tr>
                  <th className="px-4 py-3">Clause</th>
                  <th className="px-4 py-3">Requirement</th>
                  <th className="px-4 py-3">SBC Section</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filtered.map((r, i) => {
                  const cfg = BADGE[r.status];
                  const Icon = cfg.icon;
                  return (
                    <tr key={`${r.clause_code}-${i}`} className="hover:bg-slate-800/40 transition">
                      <td className="px-4 py-3 font-mono text-xs font-black text-teal-300">{r.clause_code}</td>
                      <td className="px-4 py-3">
                        <p className="text-slate-200">{r.requirement}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{r.gap_analysis}</p>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-400">{r.sbc_section ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className={`text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          r.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-300 border-rose-500/40'
                            : r.severity === 'MEDIUM' ? 'bg-amber-500/15 text-amber-300 border-amber-500/40'
                            : 'bg-slate-500/15 text-slate-300 border-slate-500/40'
                        }`}>
                          {r.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border ${cfg.cls}`}>
                          <Icon className="h-3 w-3" /> {cfg.label}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
