import React from 'react';
import { ClipboardCheck, HardHat, FileBadge, ShieldAlert, CheckCircle2, FileSignature } from 'lucide-react';

export interface ItpRecord {
  activity: string;
  reference: string;
  frequency: string;
  checkpoint: string;
}

export interface HiraRecord {
  task: string;
  hazard: string;
  probability: number;
  severity: number;
  risk_score: number;
  mitigation: string;
}

export interface QaQcHseData {
  qaqc_output?: { itp_register: ItpRecord[] };
  hse_output?: { hira_register: HiraRecord[] };
}

interface Props {
  data: QaQcHseData | null;
}

export const ItpHseStudio: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  const itpData = data.qaqc_output?.itp_register || [];
  const hseData = data.hse_output?.hira_register || [];

  return (
    <div className="bg-slate-900 rounded-lg shadow-xl border border-slate-700 mt-8 mb-8 animate-in fade-in zoom-in duration-500 overflow-hidden text-slate-100 font-sans">
      <div className="bg-black/40 p-4 border-b border-slate-700 flex justify-between items-center">
        <h3 className="text-lg font-bold flex items-center text-teal-400 tracking-wide">
          <FileBadge className="mr-3" size={22} />
          QA/QC Inspection & HSE Risk Management Studio
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-teal-900/40 text-teal-400 border border-teal-500/30 px-3 py-1.5 rounded-full shadow-sm">
          <CheckCircle2 size={14} className="mr-1.5" /> ISO 9001 / ISO 45001 Compliant
        </div>
      </div>
      
      <div className="p-6 flex flex-col xl:flex-row gap-8">
        
        {/* Left Column: ITP Register */}
        <div className="xl:w-1/2">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <ClipboardCheck size={14} className="mr-2 text-slate-400" /> Inspection & Test Plan (ITP)
          </h4>
          
          <div className="overflow-x-auto rounded-lg border border-slate-700 shadow-inner">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/90 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3 border-b border-slate-700 font-semibold">Activity</th>
                  <th className="px-4 py-3 border-b border-slate-700 font-semibold">Standard</th>
                  <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Intervention</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-slate-300 bg-slate-900/50">
                {itpData.map((itp, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3 font-bold text-slate-200 text-xs flex flex-col">
                      <span>{itp.activity}</span>
                      <span className="text-[9px] font-mono text-slate-500 mt-0.5">{itp.frequency}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-indigo-300">{itp.reference}</td>
                    <td className="px-4 py-3 flex justify-center">
                      <div className={`flex items-center text-[9px] uppercase tracking-widest font-bold px-2 py-1 rounded border shadow-sm ${
                        itp.checkpoint === 'Hold Point' ? 'text-rose-400 bg-rose-950/40 border-rose-500/40' : 
                        itp.checkpoint === 'Witness Point' ? 'text-amber-400 bg-amber-950/40 border-amber-500/40' : 
                        'text-blue-400 bg-blue-950/40 border-blue-500/40'
                      }`}>
                        {itp.checkpoint === 'Hold Point' && <ShieldAlert size={12} className="mr-1" />}
                        {itp.checkpoint === 'Witness Point' && <FileSignature size={12} className="mr-1" />}
                        {itp.checkpoint}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: HSE Matrix */}
        <div className="xl:w-1/2">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
            <HardHat size={14} className="mr-2 text-slate-400" /> HSE Risk & Hazard Matrix (HIRA)
          </h4>
          
          <div className="space-y-3">
            {hseData.map((hira, idx) => (
              <div key={idx} className="bg-slate-800/80 border border-slate-700 p-4 rounded-lg flex flex-col shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex flex-col">
                    <span className="text-sm font-bold text-slate-200 tracking-wide">{hira.task}</span>
                    <span className="text-[11px] font-medium text-rose-400 mt-1">{hira.hazard}</span>
                  </div>
                  <div className={`flex flex-col items-center justify-center p-2 rounded border ${
                    hira.risk_score >= 15 ? 'bg-rose-950/40 border-rose-500/50 text-rose-400' : 'bg-orange-950/40 border-orange-500/50 text-orange-400'
                  }`}>
                    <span className="text-[9px] uppercase font-bold tracking-widest opacity-80">Risk Score</span>
                    <span className="text-xl font-black font-mono leading-none mt-1">{hira.risk_score}</span>
                  </div>
                </div>
                
                <div className="mt-2 bg-black/30 p-2.5 rounded border border-slate-700/50 flex items-start">
                  <ShieldAlert size={14} className="mr-2 text-emerald-500 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300 leading-snug font-mono">
                    <span className="text-emerald-400 font-bold mr-1">Mitigation:</span>
                    {hira.mitigation}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
