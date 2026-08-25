import React from 'react';
import { Cpu, DollarSign, Activity, ServerCrash, ShieldCheck } from 'lucide-react';

export interface LlmMetrics {
  total_tokens: number;
  total_cost_usd: number;
  primary_model: string;
  fallback_triggered: boolean;
  models_distribution: Record<string, number>;
}

interface Props {
  data: LlmMetrics | null;
}

export const LlmUsageCard: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans h-full @container">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-wrap justify-between items-center gap-x-3 gap-y-2">
        <h3 className="text-lg font-bold flex items-center text-blue-400 tracking-wide flex-1 min-w-0">
          <Cpu className="mr-3 shrink-0" size={22} />
          <span>LLM Gateway &amp; PII Telemetry</span>
        </h3>
        <div className="flex items-center text-xs font-bold bg-emerald-900/30 px-3 py-1.5 rounded-full border border-emerald-500/30 whitespace-nowrap shrink-0">
          <ShieldCheck size={14} className="mr-1.5" /> PII Sanitizer Active
        </div>
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-1 gap-2.5 @[30rem]:grid-cols-[1fr_1fr_1.4fr]">
          
          <div className="bg-slate-800 p-3 rounded-lg border border-slate-600 shadow-inner flex items-center justify-between gap-3 min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center shrink-0">
              <Activity size={14} className="mr-2 text-slate-300 shrink-0"/> Total Tokens
            </span>
            <span className="shrink-0 whitespace-nowrap font-mono tabular-nums text-xl font-bold text-white tracking-tight">{data.total_tokens.toLocaleString()}</span>
          </div>
          
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-600 shadow-inner flex items-center justify-between gap-3 @[26rem]:flex-col @[26rem]:items-stretch @[26rem]:justify-between min-w-0">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center shrink-0">
              <DollarSign size={14} className="mr-2 text-slate-300 shrink-0"/> Est. API Cost
            </span>
            <span className="shrink-0 whitespace-nowrap font-mono tabular-nums text-xl font-bold text-emerald-400 tracking-tight">${data.total_cost_usd.toFixed(4)}</span>
          </div>

          <div className={`p-4 rounded-lg border shadow-inner flex items-center justify-between gap-3 @[26rem]:flex-col @[26rem]:items-stretch @[26rem]:justify-between min-w-0 ${data.fallback_triggered ? 'bg-orange-900/20 border-orange-500/40' : 'bg-slate-800 border-slate-600'}`}>
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center shrink-0">
              <ServerCrash size={14} className="mr-2 text-slate-300 shrink-0"/> Gateway Routing
            </span>
            <div className="flex flex-col items-end @[26rem]:items-start shrink-0 min-w-0">
              <span className="text-base font-black text-slate-200 tracking-tight whitespace-nowrap">{data.primary_model}</span>
              {data.fallback_triggered ? (
                <span className="text-[10px] font-bold text-orange-400 mt-0.5 uppercase tracking-wide bg-orange-950/50 px-2 py-0.5 rounded inline-block w-max">
                  Fallback Activated
                </span>
              ) : (
                <span className="text-[10px] font-bold text-emerald-400 mt-0.5 uppercase tracking-wide bg-emerald-950/50 px-2 py-0.5 rounded inline-block w-max">
                  100% SLA Maintained
                </span>
              )}
            </div>
          </div>

        </div>

        <div className="mt-5">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 border-b border-slate-700 pb-2">Swarm Node Model Distribution</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.models_distribution).map(([model, tokens]) => (
              <div key={model} className="bg-slate-800 px-3 py-2 rounded-full border border-slate-600 flex items-center gap-2 shadow-sm min-w-0">
                <span className="text-sm font-bold text-blue-300 truncate">{model}</span>
                <span className="text-xs text-slate-500 shrink-0">|</span>
                <span className="text-sm font-mono text-slate-300 whitespace-nowrap">{tokens.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
        
      </div>
    </div>
  );
};
