"use client";

import React from 'react';
import { Activity, ShieldAlert, HeartPulse, Server, Radio, Bot } from 'lucide-react';
import type { PlatformOverview } from '../lib/analytics_client';
import { t, getLang, type Lang } from '../lib/i18n';
import { useState, useEffect } from 'react';

interface Props {
  overview: PlatformOverview | null;
}

/** مراقب النظام الحي — حالة الوكلاء والمزودين وآخر نشاط حقيقي من سجل التدقيق. */
export const SystemHealthMonitor: React.FC<Props> = ({ overview }) => {
  const [lang, setLang] = useState<Lang>('ar');
  useEffect(() => {
    setLang(getLang());
    const onChange = (e: Event) => setLang((e as CustomEvent).detail as Lang);
    window.addEventListener('noor.lang-changed', onChange);
    return () => window.removeEventListener('noor.lang-changed', onChange);
  }, []);
  const sys = overview?.system;
  const activity = overview?.recent_activity || [];
  const p = overview?.portfolio;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans h-full @container">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex flex-wrap justify-between items-center gap-x-3 gap-y-2">
        <h3 className="text-lg font-bold flex items-center text-teal-400 tracking-wide flex-1 min-w-0">
          <Activity className="mr-3 shrink-0" size={22} />
          <span>{t("systemTelemetry", lang)}</span>
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-teal-900/40 text-teal-400 border border-teal-500/30 px-3 py-1.5 rounded-full shadow-sm shrink-0">
          <Radio size={14} className="mr-1.5 animate-pulse" /> Live
        </div>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-2 @[32rem]:grid-cols-4 gap-4 mb-6">

          <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 shadow-inner flex flex-col items-start justify-between gap-2 min-w-0 overflow-hidden">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center min-w-0">
              <HeartPulse size={14} className="mr-2 text-teal-400 shrink-0"/> {t("clusterStatus", lang)}
            </span>
            <span className="inline-flex w-fit max-w-full items-center gap-1.5 rounded-full border border-teal-500/30 bg-teal-500/15 px-3 py-1 min-w-0">
              <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-teal-400 animate-pulse" />
              <span className="whitespace-nowrap truncate text-sm font-black text-teal-300">{sys?.cluster_status ?? '—'}</span>
            </span>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 shadow-inner flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-2">
              <Bot size={14} className="mr-2 text-blue-400"/> {t("activeAgents", lang)}
            </span>
            <span className="text-2xl font-black text-white font-mono tracking-tight">{sys?.agents_enabled ?? '—'}</span>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 shadow-inner flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-2">
              <Activity size={14} className="mr-2 text-emerald-400"/> {t("swarmsRun", lang)}
            </span>
            <div className="flex items-end whitespace-nowrap">
              <span className="text-2xl font-black text-emerald-400 font-mono tracking-tight">
                {p ? p.tenders_completed + p.tenders_processing : '—'}
              </span>
            </div>
          </div>

          <div className="bg-slate-800/80 p-4 rounded-lg border border-slate-700 shadow-inner flex flex-col justify-between">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-2">
              <Server size={14} className="mr-2 text-violet-400"/> {t("providersOn", lang)}
            </span>
            <span className={`text-2xl font-black font-mono tracking-tight ${(sys?.providers_enabled ?? 0) > 0 ? 'text-white' : 'text-rose-400'}`}>
              {sys?.providers_enabled ?? '—'}
            </span>
          </div>

        </div>

        {/* Real audit-log activity */}
        <div>
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">
            {t("recentAuditActivity", lang)}
          </h4>
          {activity.length === 0 ? (
            <p className="text-sm text-slate-500 py-4 text-center">{t("noActivity", lang)}</p>
          ) : (
            <div className="flex flex-col space-y-2">
              {activity.map((a) => (
                <div key={a.id} className="bg-black/30 border border-slate-700 p-3 rounded flex items-center justify-between gap-3 shadow-sm">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className={`text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded shrink-0 ${
                      a.action === 'TRIGGER_AUDIT'
                        ? 'bg-cyan-900/40 text-cyan-300 border border-cyan-500/30'
                        : 'bg-slate-800 text-slate-300 border border-slate-600'
                    }`}>
                      {a.action}
                    </span>
                    <span className="text-sm font-medium text-slate-300 truncate">
                      Tender #{a.tender_id ?? '—'} · by {a.user}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-slate-500 whitespace-nowrap shrink-0">{a.at}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
