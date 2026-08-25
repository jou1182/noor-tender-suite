"use client";

import React, { useState } from 'react';
import { Lightbulb, TrendingDown, Hammer, CheckCircle, XCircle, ChevronDown, Sparkles, Ban, ShieldCheck } from 'lucide-react';
import { VEOpportunityCard, VESummary } from '../types/ve';

const sar = (n: number) =>
  new Intl.NumberFormat('en-SA', { style: 'currency', currency: 'SAR', maximumFractionDigits: 0 }).format(n);

function SkeletonRow() {
  return (
    <div className="animate-pulse space-y-3 p-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="flex items-center gap-4">
          <div className="h-3 w-40 rounded bg-slate-800" />
          <div className="h-3 w-48 rounded bg-slate-800" />
          <div className="h-3 w-24 rounded bg-slate-800" />
          <div className="h-3 w-24 rounded bg-slate-800" />
          <div className="h-6 w-20 rounded-full bg-slate-800" />
        </div>
      ))}
    </div>
  );
}

interface ValueEngineeringStudioProps {
  cards: VEOpportunityCard[];
  summary?: VESummary;
  loading?: boolean;
}

export const ValueEngineeringStudio: React.FC<ValueEngineeringStudioProps> = ({ cards, summary, loading = false }) => {
  const [expanded, setExpanded] = useState<string | null>(null);
  const [accepted, setAccepted] = useState<Record<string, boolean>>({});

  const recommendations = cards.filter((c) => c.is_recommended);
  const blocked = cards.filter((c) => !c.is_recommended);

  const totals: VESummary = summary ?? {
    total_potential_savings_sar: recommendations.reduce((s, c) => s + c.net_savings_sar, 0),
    net_schedule_acceleration_percent: recommendations.length
      ? recommendations.reduce((s, c) => s + c.speed_index_gain_percent, 0) / recommendations.length
      : 0,
    total_sbc_verified_proposals: recommendations.length,
    total_blocked: blocked.length,
  };

  const toggleAccept = (key: string) => setAccepted((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 mt-8 mb-8 animate-in fade-in duration-500 font-sans text-slate-100">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
        <h3 className="text-xl font-black flex items-center text-emerald-400 tracking-wide">
          <Lightbulb className="mr-3 shrink-0" size={26} />
          Value Engineering & Constructability Optimization
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-full shadow-sm shrink-0">
          <ShieldCheck size={14} className="mr-1.5" /> SBC-304 Verified
        </div>
      </div>

      <div className="p-6">
        {loading ? (
          <SkeletonRow />
        ) : (
          <>
            {/* Top Metric Header */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-800/80 p-5 rounded-lg border border-emerald-900/50 bg-emerald-950/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-emerald-500 uppercase tracking-widest font-bold">Total Potential Savings</span>
                  <TrendingDown size={16} className="text-emerald-500" />
                </div>
                <div className="text-3xl font-black font-mono text-emerald-400 whitespace-nowrap">{sar(totals.total_potential_savings_sar)}</div>
                <div className="text-xs text-emerald-600 mt-1 font-semibold">Net Value Engineering Delta (SAR)</div>
              </div>

              <div className="bg-slate-800/80 p-5 rounded-lg border border-blue-900/50 bg-blue-950/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-blue-500 uppercase tracking-widest font-bold">Net Schedule Acceleration</span>
                  <Hammer size={16} className="text-blue-500" />
                </div>
                <div className="text-3xl font-black font-mono text-blue-400 whitespace-nowrap">
                  +{totals.net_schedule_acceleration_percent.toFixed(1)}%
                </div>
                <div className="text-xs text-blue-600 mt-1 font-semibold">Average Construction Speed Gain</div>
              </div>

              <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">SBC Verified Proposals</span>
                  <CheckCircle size={16} className="text-emerald-500" />
                </div>
                <div className="text-3xl font-black font-mono text-slate-100 whitespace-nowrap">{totals.total_sbc_verified_proposals}</div>
                <div className="text-xs text-slate-500 mt-1 font-semibold">
                  {totals.total_blocked > 0 ? `${totals.total_blocked} blocked by SBC 304` : 'All candidates compliant'}
                </div>
              </div>
            </div>

            {cards.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-14 text-center border border-dashed border-slate-700 rounded-lg">
                <Lightbulb className="h-10 w-10 text-slate-600 mb-3" />
                <p className="text-sm font-semibold text-slate-400">No value-engineering candidates evaluated yet.</p>
                <p className="text-xs text-slate-600 mt-1">Run a tender audit to hydrate the optimization matrix.</p>
              </div>
            ) : (
              <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest p-4 border-b border-slate-700 bg-black/20 flex items-center">
                  Opportunity Matrix
                </h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-800/90 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                      <tr>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold">BOQ Item</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold">Original Spec</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-emerald-400">Proposed VE Alternative</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-right">Unit Delta</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-right">Total Savings</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">SBC Status</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Action</th>
                        <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center w-8" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50 text-slate-300">
                      {cards.map((card, idx) => {
                        const key = `${card.boq_item}-${idx}`;
                        const isOpen = expanded === key;
                        const isAccepted = accepted[key] ?? card.is_accepted;
                        const compliant = card.sbc_status === 'COMPLIANT';
                        return (
                          <React.Fragment key={key}>
                            <tr
                              className={`hover:bg-slate-800/50 transition-colors cursor-pointer ${!card.is_recommended ? 'opacity-80' : ''}`}
                              onClick={() => setExpanded(isOpen ? null : key)}
                            >
                              <td className="px-4 py-3 font-semibold text-slate-300">{card.boq_item}</td>
                              <td className="px-4 py-3 text-slate-500 line-through decoration-slate-600">{card.original_spec}</td>
                              <td className="px-4 py-3 font-bold text-emerald-400">{card.proposed_alternative}</td>
                              <td className="px-4 py-3 text-right font-mono text-slate-400">{sar(card.unit_delta_sar)}</td>
                              <td className="px-4 py-3 text-right font-mono text-emerald-300">{sar(card.net_savings_sar)}</td>
                              <td className="px-4 py-3 text-center">
                                {compliant ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border border-emerald-500/40 bg-emerald-500/15 text-emerald-300">
                                    <CheckCircle size={11} /> Compliant
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border border-rose-500/40 bg-rose-500/15 text-rose-300">
                                    <Ban size={11} /> Blocked
                                  </span>
                                )}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <button
                                  onClick={(e) => { e.stopPropagation(); toggleAccept(key); }}
                                  disabled={!card.is_recommended}
                                  title={card.is_recommended ? (isAccepted ? 'Reject for submittal' : 'Accept for submittal') : 'Blocked by SBC 304'}
                                  className={`inline-flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border transition disabled:opacity-40 disabled:cursor-not-allowed ${
                                    isAccepted
                                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                                      : 'bg-slate-900/40 text-slate-400 border-slate-700 hover:text-slate-200'
                                  }`}
                                >
                                  {isAccepted ? <CheckCircle size={13} /> : <XCircle size={13} />}
                                  {isAccepted ? 'Accepted' : 'Reject'}
                                </button>
                              </td>
                              <td className="px-4 py-3 text-center">
                                <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                              </td>
                            </tr>
                            {isOpen && (
                              <tr className="bg-slate-950/60">
                                <td colSpan={8} className="px-6 py-4">
                                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                    <div>
                                      <p className={`text-[10px] font-black uppercase tracking-widest mb-2 flex items-center gap-1.5 ${card.is_recommended ? 'text-emerald-400' : 'text-rose-400'}`}>
                                        <Sparkles className="h-3.5 w-3.5" /> Technical Justification
                                      </p>
                                      <p className="text-sm text-slate-300 leading-relaxed">{card.technical_justification}</p>
                                    </div>
                                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/10 p-3">
                                      <p className="text-[10px] font-black uppercase tracking-widest text-emerald-300 mb-2 flex items-center gap-1.5">
                                        <ShieldCheck className="h-3.5 w-3.5" /> SBC 304 Clause References
                                      </p>
                                      <div className="flex flex-wrap gap-1.5">
                                        {card.sbc_304_references.length > 0 ? (
                                          card.sbc_304_references.map((ref) => (
                                            <span key={ref} className="text-[10px] font-mono font-bold bg-emerald-950/40 border border-emerald-900/40 text-emerald-300 px-2 py-0.5 rounded-full">
                                              {ref}
                                            </span>
                                          ))
                                        ) : (
                                          <span className="text-xs text-slate-500 italic">No clause references recorded.</span>
                                        )}
                                      </div>
                                      <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                                        <span className="font-mono">Δ/unit: {sar(card.unit_delta_sar)}</span>
                                        <span className="text-slate-600">|</span>
                                        <span className="font-mono">Speed gain: +{card.speed_index_gain_percent}%</span>
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
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};