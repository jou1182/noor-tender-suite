import React from 'react';
import { BrainCircuit, TrendingUp, AlertOctagon, History, Target } from 'lucide-react';

export interface HistoricalRisk {
  tender_id: string;
  outcome: string;
  lesson_learned: string;
}

export interface InstitutionalMemoryData {
  client_name: string;
  historic_conversion_rate: string;
  win_improvement_yoy: string;
  historic_risks: HistoricalRisk[];
}

interface Props {
  data: InstitutionalMemoryData | null;
}

export const WinLossAnalyticsCard: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  const formatClientName = (name: string) => {
    return name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 mt-8 mb-8 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold flex items-center text-purple-400 tracking-wide">
          <BrainCircuit className="mr-3" size={22} />
          Institutional Memory & Bid Outcome Feedback Loop
        </h3>
      </div>
      
      <div className="p-6">
        {/* Top Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-slate-800 p-5 rounded-lg border border-slate-600 shadow-inner flex flex-col justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-3">
              <Target size={14} className="mr-2 text-purple-400"/> Current Client Target
            </span>
            <span className="text-2xl font-black text-white tracking-tight">{formatClientName(data.client_name)}</span>
          </div>
          
          <div className="bg-slate-800 p-5 rounded-lg border border-slate-600 shadow-inner flex flex-col justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-3">
              <History size={14} className="mr-2 text-slate-300"/> Historic Conversion Rate
            </span>
            <span className="text-3xl font-black text-emerald-400 font-mono tracking-tight">{data.historic_conversion_rate}</span>
          </div>

          <div className="bg-slate-800 p-5 rounded-lg border border-slate-600 shadow-inner flex flex-col justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest flex items-center mb-3">
              <TrendingUp size={14} className="mr-2 text-slate-300"/> Win-Rate Optimization
            </span>
            <div className="flex items-end">
              <span className="text-3xl font-black text-blue-400 font-mono tracking-tight">{data.win_improvement_yoy}</span>
              <span className="text-xs text-slate-500 ml-2 mb-1.5 uppercase font-bold tracking-widest">YoY Trend</span>
            </div>
          </div>
        </div>

        {/* Vulnerability Warnings (Proactive Guardrails) */}
        <div>
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2">
            Proactive Subsystem Guardrails (Derived from {formatClientName(data.client_name)} historical data)
          </h4>
          <div className="flex flex-col space-y-4">
            {data.historic_risks.length === 0 ? (
              <div className="text-slate-400 text-sm font-medium italic bg-slate-800/50 p-4 rounded border border-slate-700/50">
                No historic disqualifications or lost records found for this client.
              </div>
            ) : (
              data.historic_risks.map((risk, idx) => (
                <div key={idx} className="bg-orange-950/20 border border-orange-500/30 p-5 rounded-lg flex items-start shadow-sm">
                  <AlertOctagon className="text-orange-500 mr-4 shrink-0 mt-0.5" size={22} />
                  <div>
                    <div className="flex items-center space-x-3 mb-1.5">
                      <span className="text-[11px] font-bold text-orange-400 uppercase tracking-widest bg-orange-900/40 px-2 py-0.5 rounded border border-orange-500/20">
                        Previous {risk.outcome}
                      </span>
                      <span className="text-[11px] font-mono font-bold text-slate-400 tracking-wider">Ref: {risk.tender_id}</span>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed font-medium mt-1">
                      {risk.lesson_learned}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
