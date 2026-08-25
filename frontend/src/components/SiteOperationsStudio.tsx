import React from 'react';
import { Mic, Camera, AlertOctagon, FileWarning, HardHat, CheckCircle2 } from 'lucide-react';

export interface FieldNcr {
  ncr_id: string;
  defect_type: string;
  sbc_violation_code: string;
  violation_desc: string;
  severity: "CRITICAL" | "MODERATE";
  status: string;
  required_action: string;
}

export interface FieldData {
  transcript_processed: string;
  vision_tags_processed: string[];
  ncrs_issued: FieldNcr[];
  total_defects: number;
  timestamp: string;
}

interface SiteOperationsStudioProps {
  data: FieldData;
}

export const SiteOperationsStudio: React.FC<SiteOperationsStudioProps> = ({ data }) => {
  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border border-slate-700 mt-8 mb-8 animate-in fade-in duration-500 font-sans text-slate-100">
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center">
        <h3 className="text-xl font-black flex items-center text-amber-500 tracking-wide">
          <HardHat className="mr-3" size={26} />
          Multimodal Field Operations & Site Inspector
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-amber-900/40 text-amber-400 border border-amber-500/30 px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0">
          <AlertOctagon size={14} className="mr-1.5" /> {data.total_defects} Defects Detected
        </div>
      </div>
      
      <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Multimodal Feed Panel */}
        <div className="col-span-1 space-y-4">
          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center border-b border-slate-700 pb-2">
              <Mic size={14} className="mr-2 text-blue-400" /> Audio Transcript Log
            </h4>
            <p className="text-sm text-slate-300 italic border-l-2 border-blue-500 pl-3 bg-slate-900/50 py-2">
              "{data.transcript_processed}"
            </p>
          </div>
          
          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center border-b border-slate-700 pb-2">
              <Camera size={14} className="mr-2 text-indigo-400" /> AI Vision Classifications
            </h4>
            <div className="flex flex-wrap gap-2 mt-2">
              {data.vision_tags_processed.map((tag, idx) => (
                <span key={idx} className="bg-indigo-950/40 text-indigo-400 border border-indigo-500/30 text-xs px-2.5 py-1 rounded-md font-mono font-bold">
                  [{tag}]
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Structural NCR Viewer */}
        <div className="col-span-1 lg:col-span-2">
          <div className="bg-slate-800/50 p-5 rounded-lg border border-slate-700 h-full">
             <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4 flex items-center border-b border-slate-700 pb-2">
              <FileWarning size={14} className="mr-2 text-rose-400" /> Automated Non-Conformance Reports (NCR)
            </h4>
            
            {data.ncrs_issued.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-48 text-slate-500">
                <CheckCircle2 size={48} className="text-emerald-500 mb-3 opacity-60" />
                <p className="font-bold text-sm">Site Clear. No Defects Registered.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.ncrs_issued.map((ncr, idx) => (
                  <div key={idx} className={`p-4 rounded border ${ncr.severity === 'CRITICAL' ? 'bg-rose-950/20 border-rose-900/50' : 'bg-amber-950/20 border-amber-900/50'}`}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-mono text-sm font-bold text-slate-200">{ncr.ncr_id}</div>
                      <div className={`text-[10px] font-black tracking-widest px-2 py-0.5 rounded uppercase ${ncr.severity === 'CRITICAL' ? 'bg-rose-600 text-white' : 'bg-amber-600 text-white'}`}>
                        {ncr.severity}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">Defect Classification</span>
                        <span className="text-slate-300 font-semibold">{ncr.defect_type}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 block text-[9px] uppercase">SBC / OSHA Code Reference</span>
                        <span className="text-blue-400 font-mono font-bold">{ncr.sbc_violation_code}</span>
                      </div>
                    </div>
                    
                    <div className="bg-slate-900/50 p-2 rounded text-xs border border-slate-700/50">
                      <span className="text-slate-400 block mb-1">Mandatory Resolution Action:</span>
                      <span className="text-slate-200 font-semibold">{ncr.required_action}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        
      </div>
    </div>
  );
};
