import React from 'react';
import { Box, Layers, AlertTriangle, CheckCircle, Database } from 'lucide-react';

export interface VarianceItem {
  item: string;
  bim_quantity: number;
  boq_quantity: number;
  variance_absolute: number;
  variance_pct: number;
  flagged: boolean;
  warning: string;
}

export interface BimData {
  model_status: string;
  element_count: number;
  takeoff_variances: VarianceItem[];
}

interface Props {
  data: BimData | null;
}

export const BimModelViewer: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 mt-8 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold flex items-center text-cyan-400 tracking-wide">
          <Box className="mr-3" />
          BIM IFC 4D/5D Quantity Takeoff Engine
        </h3>
        <div className="flex items-center space-x-4">
          <span className="text-xs font-mono text-slate-400">Elements: {data.element_count.toLocaleString()}</span>
          <span className="text-[11px] uppercase tracking-widest font-bold bg-cyan-900/40 text-cyan-400 border border-cyan-500/30 px-3 py-1.5 rounded-full shadow-sm">
            {data.model_status}
          </span>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row min-h-[400px]">
        {/* WebGL Viewport HUD Simulation */}
        <div className="lg:w-1/2 bg-black relative border-r border-slate-700 overflow-hidden flex items-center justify-center min-h-[350px]">
          <div className="absolute inset-0 opacity-20" style={{
            backgroundImage: 'linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)',
            backgroundSize: '24px 24px'
          }}></div>
          
          <div className="absolute top-4 left-4 flex flex-col space-y-3 z-20">
            <div className="bg-slate-900/90 border border-slate-600 p-2.5 rounded shadow-lg flex flex-col items-center">
               <Layers size={18} className="text-cyan-400 mb-1.5" />
               <span className="text-[9px] uppercase tracking-widest font-bold text-slate-300">IFC Structure</span>
            </div>
            <div className="bg-slate-900/90 border border-slate-600 p-2.5 rounded shadow-lg flex flex-col items-center">
               <Database size={18} className="text-emerald-400 mb-1.5" />
               <span className="text-[9px] uppercase tracking-widest font-bold text-slate-300">5D BOQ Sync</span>
            </div>
          </div>

          <div className="relative z-10 flex flex-col items-center">
             <div className="w-40 h-40 border-2 border-cyan-500/50 rounded-xl transform rotate-45 flex items-center justify-center shadow-[0_0_40px_rgba(6,182,212,0.25)] animate-pulse">
                <div className="w-20 h-20 border-2 border-cyan-400/80 rounded-lg transform -rotate-12 bg-cyan-900/20 backdrop-blur-sm"></div>
             </div>
             <span className="mt-10 text-[10px] font-mono text-cyan-500 bg-black/60 px-3 py-1.5 rounded border border-cyan-900/80 tracking-widest uppercase">WebGL / Three.js Render Active</span>
          </div>
        </div>

        {/* Variance Breakdown Table */}
        <div className="lg:w-1/2 p-0 bg-slate-900/50 flex flex-col">
          <div className="p-4 border-b border-slate-700 bg-slate-800/40">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-widest">BIM Takeoff vs BOQ Variance Matrix</h4>
          </div>
          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-sm h-full">
              <thead className="bg-slate-800/60 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3 border-b border-slate-700 font-semibold">Cost Component</th>
                  <th className="px-5 py-3 border-b border-slate-700 font-semibold text-right">IFC Engine</th>
                  <th className="px-5 py-3 border-b border-slate-700 font-semibold text-right">Client BOQ</th>
                  <th className="px-5 py-3 border-b border-slate-700 font-semibold text-right">Delta %</th>
                  <th className="px-5 py-3 border-b border-slate-700 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-slate-300">
                {data.takeoff_variances.map((variance, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-5 py-4 font-bold text-slate-200 text-xs tracking-wide">{variance.item.replace(/_/g, ' ')}</td>
                    <td className="px-5 py-4 font-mono text-right text-cyan-200">{variance.bim_quantity.toLocaleString()}</td>
                    <td className="px-5 py-4 font-mono text-right">{variance.boq_quantity.toLocaleString()}</td>
                    <td className="px-5 py-4 font-mono text-right">
                      <span className={variance.flagged ? 'text-rose-400 font-bold' : 'text-emerald-400'}>
                        {variance.variance_pct > 0 ? '+' : ''}{variance.variance_pct}%
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {variance.flagged ? (
                        <div className="flex items-center w-max text-[10px] uppercase tracking-wide font-bold text-rose-400 bg-rose-900/20 px-2.5 py-1 rounded border border-rose-500/30">
                          <AlertTriangle size={12} className="mr-1.5" /> &gt;5% Variance
                        </div>
                      ) : (
                        <div className="flex items-center w-max text-[10px] uppercase tracking-wide font-bold text-emerald-400 bg-emerald-900/20 px-2.5 py-1 rounded border border-emerald-500/30">
                          <CheckCircle size={12} className="mr-1.5" /> Validated
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
