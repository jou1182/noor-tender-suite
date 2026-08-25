import React from 'react';
import { FileSearch, CheckCircle2, AlertTriangle, XCircle, Beaker } from 'lucide-react';

export interface SubmittalParameter {
  name: string;
  required_value: number;
  submitted_value: number;
  operator: string;
  unit: string;
  passed: boolean;
}

export interface SubmittalData {
  material_name: string;
  review_status: "CODE_A" | "CODE_B" | "CODE_C" | "CODE_D";
  review_action: string;
  parameters_evaluated: SubmittalParameter[];
  discrepancies_found: number;
  technical_commentary: string[];
}

interface SubmittalReviewStudioProps {
  data: SubmittalData;
}

export const SubmittalReviewStudio: React.FC<SubmittalReviewStudioProps> = ({ data }) => {
  
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'CODE_A': return { color: 'text-emerald-400', bg: 'bg-emerald-950/20', border: 'border-emerald-900/50', icon: <CheckCircle2 className="mr-3 text-emerald-400" size={26} /> };
      case 'CODE_B': return { color: 'text-blue-400', bg: 'bg-blue-950/20', border: 'border-blue-900/50', icon: <CheckCircle2 className="mr-3 text-blue-400" size={26} /> };
      case 'CODE_C': return { color: 'text-amber-400', bg: 'bg-amber-950/20', border: 'border-amber-900/50', icon: <AlertTriangle className="mr-3 text-amber-400" size={26} /> };
      case 'CODE_D': return { color: 'text-rose-400', bg: 'bg-rose-950/20', border: 'border-rose-900/50', icon: <XCircle className="mr-3 text-rose-400" size={26} /> };
      default: return { color: 'text-slate-400', bg: 'bg-slate-900', border: 'border-slate-700', icon: <FileSearch className="mr-3" size={26} /> };
    }
  };

  const config = getStatusConfig(data.review_status);

  return (
    <div className={`rounded-lg shadow-2xl border mt-8 mb-8 animate-in fade-in duration-500 font-sans text-slate-100 ${config.bg} ${config.border}`}>
      <div className={`p-5 border-b flex flex-col md:flex-row justify-between items-start md:items-center ${config.border} bg-black/40`}>
        <h3 className={`text-xl font-black flex items-center tracking-wide ${config.color}`}>
          {config.icon}
          Material Submittal & Technical Data Review
        </h3>
        <div className={`flex items-center text-[10px] uppercase tracking-widest font-bold px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0 ${config.bg} ${config.color} border ${config.border}`}>
          <FileSearch size={14} className="mr-1.5" /> Official Transmittal Form
        </div>
      </div>
      
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Status Action Card */}
        <div className="col-span-1 space-y-4">
          <div className={`p-6 rounded-lg border flex flex-col items-center justify-center text-center h-full shadow-inner ${config.bg} ${config.border}`}>
             <div className="text-[10px] font-black uppercase tracking-widest mb-2 text-slate-400">Transmittal Review Status</div>
             <div className={`text-6xl font-black mb-2 ${config.color}`}>{data.review_status.replace('CODE_', '')}</div>
             <div className={`text-lg font-bold uppercase tracking-widest ${config.color}`}>{data.review_action}</div>
             
             <div className="mt-6 w-full text-left bg-black/30 p-3 rounded border border-slate-700/50">
               <span className="text-[9px] uppercase tracking-widest font-bold text-slate-500 block mb-1">Technical Commentary</span>
               <ul className="space-y-1 text-xs text-slate-300 font-semibold">
                 {data.technical_commentary.map((comment, idx) => (
                   <li key={idx} className={comment.includes('CRITICAL') || comment.includes('FATAL') ? 'text-rose-400' : ''}>
                     • {comment}
                   </li>
                 ))}
               </ul>
             </div>
          </div>
        </div>

        {/* Spec Comparison Matrix */}
        <div className="col-span-1 lg:col-span-2">
          <div className="bg-slate-800/80 rounded-lg border border-slate-700 h-full overflow-hidden shadow-inner">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest p-4 border-b border-slate-700 bg-black/20 flex items-center">
              <Beaker size={14} className="mr-2 text-blue-400" /> {data.material_name}
            </h4>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/50 text-slate-400 font-mono text-[10px] uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3 border-b border-slate-700 font-semibold w-1/3">Technical Parameter</th>
                    <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Project Spec Requirement</th>
                    <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Manufacturer TDS Submitted</th>
                    <th className="px-4 py-3 border-b border-slate-700 font-semibold text-center">Variance / Compliance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50 text-slate-300">
                  {data.parameters_evaluated.map((param, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/50 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-200">{param.name}</td>
                      <td className="px-4 py-3 text-center font-mono">
                        {param.operator} {param.required_value} <span className="text-[9px] text-slate-500">{param.unit}</span>
                      </td>
                      <td className="px-4 py-3 text-center font-mono font-bold text-indigo-300">
                        {param.submitted_value} <span className="text-[9px] text-indigo-500">{param.unit}</span>
                      </td>
                      <td className="px-4 py-3 flex justify-center items-center">
                        {param.passed ? (
                          <span className="bg-emerald-950/40 text-emerald-400 border border-emerald-900/50 text-[10px] uppercase font-bold tracking-widest px-2 py-1 rounded flex items-center">
                            <CheckCircle2 size={12} className="mr-1" /> Compliant
                          </span>
                        ) : (
                          <span className="bg-rose-950/40 text-rose-400 border border-rose-900/50 text-[10px] uppercase font-bold tracking-widest px-2 py-1 rounded flex items-center">
                            <AlertTriangle size={12} className="mr-1" /> Rejected
                          </span>
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
    </div>
  );
};
