import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { CalendarClock, ShieldAlert, CheckCircle2, AlertTriangle, Dice5 } from 'lucide-react';

export interface DcmaMetric {
  check: string;
  value_pct: number;
  threshold: number;
  passed: boolean;
  description: string;
}

export interface MonteCarloData {
  p50_days: number;
  p80_days: number;
  p90_days: number;
  distribution_curve: Array<{ duration: number; probability: number }>;
}

export interface ScheduleHealthData {
  dcma_results: {
    overall_status: string;
    metrics: DcmaMetric[];
  };
  monte_carlo: MonteCarloData;
}

interface Props {
  data: ScheduleHealthData | null;
}

export const ScheduleHealthStudio: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 mt-8 mb-8 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold flex items-center text-amber-500 tracking-wide">
          <CalendarClock className="mr-3" size={22} />
          DCMA 14-Point Integrity & Monte Carlo P80 Simulator
        </h3>
        <div className={`flex items-center text-[10px] uppercase tracking-widest font-bold px-3 py-1.5 rounded-full shadow-sm ${data.dcma_results.overall_status === 'PASSED' ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-500/30' : 'bg-rose-900/40 text-rose-400 border border-rose-500/30'}`}>
          {data.dcma_results.overall_status === 'PASSED' ? <CheckCircle2 size={14} className="mr-1.5" /> : <ShieldAlert size={14} className="mr-1.5" />}
          Network Status: {data.dcma_results.overall_status}
        </div>
      </div>
      
      <div className="p-6 flex flex-col xl:flex-row gap-8">
        
        {/* Left Column: DCMA 14-Point Checklist */}
        <div className="xl:w-1/2">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <ShieldAlert size={14} className="mr-2 text-slate-400" /> DCMA Core Logic Diagnostics
          </h4>
          <div className="space-y-3">
            {data.dcma_results.metrics.map((metric, idx) => (
              <div key={idx} className="bg-slate-800/80 border border-slate-700 p-3 rounded-lg flex items-center justify-between shadow-sm hover:bg-slate-800 transition-colors">
                <div className="flex flex-col">
                  <span className="text-sm font-bold text-slate-200">{metric.check}</span>
                  <span className="text-[10px] text-slate-500">{metric.description}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-lg font-mono font-black text-slate-300">{metric.value_pct.toFixed(1)}%</span>
                  {metric.passed ? (
                    <div className="bg-emerald-900/30 p-1.5 rounded text-emerald-400"><CheckCircle2 size={16} /></div>
                  ) : (
                    <div className="bg-rose-900/30 p-1.5 rounded text-rose-400"><AlertTriangle size={16} /></div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Monte Carlo Engine */}
        <div className="xl:w-1/2">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <Dice5 size={14} className="mr-2 text-slate-400" /> Probabilistic Completion (5,000 Iterations)
          </h4>
          
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700 shadow-inner flex flex-col items-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">P50 Base</span>
              <span className="text-xl font-mono font-bold text-blue-400">{data.monte_carlo.p50_days} d</span>
            </div>
            <div className="bg-indigo-900/20 p-3 rounded-lg border border-indigo-500/30 shadow-inner flex flex-col items-center ring-1 ring-indigo-500/20">
              <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest mb-1 flex items-center">Target P80</span>
              <span className="text-2xl font-mono font-black text-indigo-400">{data.monte_carlo.p80_days} d</span>
            </div>
            <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700 shadow-inner flex flex-col items-center">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">P90 Guard</span>
              <span className="text-xl font-mono font-bold text-rose-400">{data.monte_carlo.p90_days} d</span>
            </div>
          </div>

          <div className="h-64 w-full bg-black/30 rounded-lg border border-slate-700 p-4 relative shadow-inner">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.monte_carlo.distribution_curve} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorProb" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#818cf8" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#818cf8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="duration" stroke="#475569" fontSize={10} tickFormatter={(val) => `${val}d`} />
                <YAxis stroke="#475569" fontSize={10} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '4px' }}
                  itemStyle={{ color: '#c7d2fe', fontWeight: 'bold' }}
                />
                <Area type="monotone" dataKey="probability" stroke="#818cf8" strokeWidth={2} fillOpacity={1} fill="url(#colorProb)" />
                <ReferenceLine x={data.monte_carlo.p80_days} stroke="#f43f5e" strokeDasharray="3 3" label={{ position: 'top', value: 'P80 Boundary', fill: '#f43f5e', fontSize: 10, fontWeight: 'bold' }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
};
