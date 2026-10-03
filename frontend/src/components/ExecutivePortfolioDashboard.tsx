"use client";

import React from 'react';
import { TrendingUp, AlertTriangle, FileCheck, FolderKanban, DownloadCloud } from 'lucide-react';
import type { PlatformOverview } from '../lib/analytics_client';
import { t, getLang, type Lang } from '../lib/i18n';
import { useState, useEffect } from 'react';

interface Props {
  overview: PlatformOverview | null;
}

/** بطاقة المحفظة الحية — أرقام حقيقية من قاعدة البيانات، لا placeholders. */
export const ExecutivePortfolioDashboard: React.FC<Props> = ({ overview }) => {
  const [lang, setLang] = useState<Lang>('ar');
  useEffect(() => {
    setLang(getLang());
    const onChange = (e: Event) => setLang((e as CustomEvent).detail as Lang);
    window.addEventListener('noor.lang-changed', onChange);
    return () => window.removeEventListener('noor.lang-changed', onChange);
  }, []);
  const p = overview?.portfolio;
  const dist: Record<string, number> = overview?.compliance_distribution || {};
  const totalRecords: number = Object.values(dist).reduce((a, b) => a + b, 0);

  const compliant = (dist['Compliant'] || dist['Pass'] || 0);
  const gap = (dist['Gap'] || 0) + (dist['Minor Deviation'] || 0);
  const fail = (dist['Fail'] || dist['Critical Gap'] || 0);

  const segments = [
    { label: 'Compliant', value: compliant, cls: 'bg-emerald-500' },
    { label: 'Gap / Minor', value: gap, cls: 'bg-amber-500' },
    { label: 'Critical', value: fail, cls: 'bg-rose-500' },
  ].filter((s) => s.value > 0);

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 animate-in fade-in duration-500 text-slate-100 font-sans h-full @container">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-wrap justify-between items-center gap-x-3 gap-y-2">
        <h3 className="text-xl font-black flex items-center text-amber-400 tracking-wide flex-1 min-w-0">
          <TrendingUp className="mr-3 shrink-0" size={26} />
          <span>{t("portfolioLive", lang)}</span>
        </h3>
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400 border border-slate-600 rounded-full px-3 py-1.5">
          {t("computedFromData", lang)}
        </span>
      </div>

      <div className="p-6">
        {/* KPI Row */}
        <div className="grid grid-cols-2 @[40rem]:grid-cols-4 gap-3 mb-8">
          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">{t("totalTenders", lang)}</span>
              <FolderKanban size={16} className="text-teal-400" />
            </div>
            <div className="whitespace-nowrap font-mono tabular-nums text-3xl font-black text-slate-100">{p?.tenders_total ?? '—'}</div>
            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider font-bold">
              {p ? `${p.tenders_completed} completed · ${p.tenders_processing} running · ${p.tenders_draft} draft` : ''}
            </p>
          </div>

          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">{t("avgTechScore", lang)}</span>
              <FileCheck size={16} className="text-blue-400" />
            </div>
            <div className="whitespace-nowrap font-mono tabular-nums text-3xl font-black text-slate-100">
              {p?.avg_technical_score != null ? p.avg_technical_score : '—'}
            </div>
            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider font-bold">
              {p ? `across ${p.scored_tenders} audited tenders` : ''}
            </p>
          </div>

          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">{t("docsIngested", lang)}</span>
              <DownloadCloud size={16} className="text-violet-400" />
            </div>
            <div className="whitespace-nowrap font-mono tabular-nums text-3xl font-black text-slate-100">{p?.documents_ingested ?? '—'}</div>
            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider font-bold">
              {p ? `${p.compliance_records} compliance records` : ''}
            </p>
          </div>

          <div className="bg-amber-950/20 p-5 rounded-lg border border-amber-900/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-amber-500 uppercase tracking-widest font-bold">{t("criticalGaps", lang)}</span>
              <AlertTriangle size={16} className="text-amber-500" />
            </div>
            <div className="whitespace-nowrap font-mono tabular-nums text-3xl font-black text-amber-500">{fail}</div>
            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider font-bold">across all tenders</p>
          </div>
        </div>

        {/* Compliance distribution — real records only */}
        <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2">
            {t("complianceDistribution", lang)} ({totalRecords})
          </h4>
          {totalRecords === 0 ? (
            <p className="text-sm text-slate-500 py-4 text-center">
              {t("noAuditYet", lang)}
            </p>
          ) : (
            <>
              <div className="w-full h-4 bg-slate-900 rounded-full overflow-hidden flex shadow-inner">
                {segments.map((s) => (
                  <div key={s.label} className={`h-full ${s.cls}`} style={{ width: `${(s.value / totalRecords) * 100}%` }} title={`${s.label}: ${s.value}`} />
                ))}
              </div>
              <div className="flex flex-wrap justify-between gap-3 text-[10px] text-slate-400 font-bold uppercase mt-3">
                {segments.map((s) => (
                  <div key={s.label} className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${s.cls}`} /> {s.label}
                    <span className="font-mono text-slate-300">{s.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  );
};
