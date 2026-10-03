"use client";

import React, { useState } from 'react';
import {
  PenLine, Copy, Check, Loader2, FileCheck2, ClipboardList,
  Sparkles, AlertTriangle, Languages,
} from 'lucide-react';

const API = 'http://localhost:8000';
import { t, getLang, type Lang } from '../lib/i18n';
import { useState as useReactState, useEffect as useReactEffect } from 'react';

interface DraftSection {
  requirement_id: number;
  requirement_type: 'MANDATORY' | 'WEIGHTED' | 'DISQUALIFICATION';
  clause_ref: string;
  weight: number | null;
  requirement_text: string;
  draft_response: string;
  llm_enriched: boolean;
}

interface MethodSkeleton {
  trade: string;
  title: string;
  sections: string[];
}

interface DraftPackage {
  tender_id: number;
  language: string;
  sections: DraftSection[];
  method_statements: MethodSkeleton[];
  checklist: { item: string; source: string; note: string }[];
  llm_enriched: boolean;
  message?: string;
}

const TYPE_META: Record<string, { label: string; cls: string }> = {
  MANDATORY: { label: 'إلزامي / Mandatory', cls: 'bg-blue-500/15 text-blue-300 border-blue-500/40' },
  WEIGHTED: { label: 'وزني / Weighted', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
  DISQUALIFICATION: { label: 'استبعاد / Disqualifier', cls: 'bg-rose-500/15 text-rose-300 border-rose-500/40' },
};

export const ProposalDraftingStudio: React.FC<{ tenderId: number }> = ({ tenderId }) => {
  const [lang, setLang] = useReactState<Lang>('ar');
  useReactEffect(() => {
    setLang(getLang());
    const onChange = (e: Event) => setLang((e as CustomEvent).detail as Lang);
    window.addEventListener('noor.lang-changed', onChange);
    return () => window.removeEventListener('noor.lang-changed', onChange);
  }, []);
  const [draft, setDraft] = useState<DraftPackage | null>(null);
  const [loading, setLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = async (enrich: boolean) => {
    if (enrich) { setEnriching(true); } else { setLoading(true); }
    try {
      const res = await fetch(`${API}/api/v1/drafting/${tenderId}${enrich ? '/enrich' : ''}`);
      const data: DraftPackage = await res.json();
      setDraft(data);
    } finally {
      if (enrich) { setEnriching(false); } else { setLoading(false); }
    }
  };

  React.useEffect(() => { void load(false); }, [tenderId]);

  const copy = async (text: string, key: string) => {
    try { await navigator.clipboard.writeText(text); } catch { /* noop */ }
    setCopied(key);
    setTimeout(() => setCopied((c) => (c === key ? null : c)), 1600);
  };

  return (
    <div className="rounded-lg shadow-2xl border bg-slate-900 border-slate-700 p-5 space-y-5 text-slate-100">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shrink-0">
            <PenLine className="h-4 w-4 text-white" />
          </span>
          <div>
            <h2 className="text-lg font-black text-white leading-tight">{t("draftingAssistant", lang)}</h2>
            <p className="text-xs text-slate-400">
              Compliance responses, method-statement skeletons &amp; document checklist — drafted from the pinned criteria.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {draft?.llm_enriched && (
            <span className="text-[10px] font-black uppercase tracking-wider bg-violet-500/15 text-violet-300 border border-violet-500/40 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Sparkles size={11} /> LLM Enriched
            </span>
          )}
          <button onClick={() => load(true)} disabled={enriching || loading}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-2 rounded-lg border border-violet-500/40 text-violet-300 hover:bg-violet-500/10 disabled:opacity-50 transition">
            {enriching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {t("llmEnrich", lang)}
          </button>
          <button onClick={() => load(false)} disabled={loading}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-2 rounded-lg border border-slate-600 text-slate-300 hover:bg-slate-800 disabled:opacity-50 transition">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Languages className="h-4 w-4" />}
            {t("regenerate", lang)}
          </button>
        </div>
      </div>

      {loading || enriching ? (
        <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="h-16 rounded-lg bg-slate-800/60 animate-pulse" />)}</div>
      ) : !draft || draft.sections.length === 0 ? (
        <div className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center">
          <AlertTriangle className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-300" dir="auto">{draft?.message || 'No binding requirements pinned yet.'}</p>
          <p className="text-xs text-slate-500 mt-1">Pin the evaluation-criteria document in the Document Library above first.</p>
        </div>
      ) : (
        <>
          {/* Response matrix */}
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-950/60">
                <tr>
                  <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest w-32">Type</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">RFP Requirement</th>
                  <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Draft Response</th>
                  <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-16">Copy</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 bg-slate-900/40">
                {draft.sections.map((s) => {
                  const meta = TYPE_META[s.requirement_type];
                  const key = `sec-${s.requirement_id}`;
                  return (
                    <tr key={key} className="hover:bg-slate-800/40 align-top transition">
                      <td className="px-3 py-3">
                        <span className={`inline-block text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${meta.cls}`}>{meta.label}</span>
                        {s.weight != null && <div className="mt-1 text-[10px] font-mono text-slate-500">{s.weight}%</div>}
                      </td>
                      <td className="px-3 py-3 text-xs text-slate-300 max-w-[240px]" dir="auto">{s.requirement_text}</td>
                      <td className="px-3 py-3 text-xs text-slate-200 leading-relaxed max-w-[420px]" dir="auto">
                        {s.draft_response.length > 180 && expanded !== key && expanded !== key + '-full'
                          ? s.draft_response.slice(0, 180) + '… '
                          : s.draft_response}
                        {s.draft_response.length > 180 && (
                          <button onClick={() => setExpanded(expanded ? null : key + '-full')}
                            className="text-teal-400 font-bold ml-1 hover:text-teal-300">
                            {expanded ? 'less' : 'more'}
                          </button>
                        )}
                        {s.llm_enriched && (
                          <span className="ml-2 text-[9px] font-black uppercase text-violet-300 bg-violet-500/15 border border-violet-500/40 px-1.5 py-0.5 rounded">LLM</span>
                        )}
                      </td>
                      <td className="px-3 py-3 text-center">
                        <button onClick={() => copy(s.draft_response, key)} title="Copy to proposal"
                          className="p-1.5 rounded-lg border border-slate-700 text-slate-400 hover:text-teal-300 hover:border-teal-500/50 transition">
                          {copied === key ? <Check className="h-4 w-4 text-emerald-400" /> : <Copy className="h-4 w-4" />}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            {/* Method skeletons */}
            <div className="rounded-lg border border-slate-800 overflow-hidden">
              <h4 className="text-xs font-black uppercase tracking-widest p-3 border-b border-slate-800 bg-slate-950/60 flex items-center gap-1.5 text-teal-300">
                <PenLine size={13} /> Method Statement Skeletons
              </h4>
              <div className="divide-y divide-slate-800/70">
                {draft.method_statements.map((m) => (
                  <div key={m.trade} className="p-3">
                    <p className="text-sm font-bold text-slate-100" dir="auto">{m.title}</p>
                    <div className="mt-1.5 flex flex-wrap gap-1">
                      {m.sections.map((s) => (
                        <span key={s} className="text-[10px] font-mono bg-slate-800/80 border border-slate-700 text-slate-300 px-2 py-0.5 rounded-full">{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Document checklist */}
            <div className="rounded-lg border border-slate-800 overflow-hidden">
              <h4 className="text-xs font-black uppercase tracking-widest p-3 border-b border-slate-800 bg-slate-950/60 flex items-center gap-1.5 text-teal-300">
                <ClipboardList size={13} /> Document Checklist ({draft.checklist.length})
              </h4>
              <div className="divide-y divide-slate-800/70 max-h-64 overflow-y-auto">
                {draft.checklist.length === 0 ? (
                  <p className="p-4 text-xs text-slate-500 italic">No attachment requirements detected in the pinned criteria.</p>
                ) : draft.checklist.map((c, i) => (
                  <div key={i} className="p-3 flex items-start gap-2">
                    <FileCheck2 className="h-4 w-4 text-teal-400 shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-xs font-semibold text-slate-200" dir="auto">{c.item}</p>
                      <p className="text-[10px] text-slate-500" dir="auto">{c.source} — {c.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
