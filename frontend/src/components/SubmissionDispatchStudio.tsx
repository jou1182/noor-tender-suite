import React from 'react';
import { Send, ShieldCheck, FileKey, CheckCircle2, ShieldAlert } from 'lucide-react';

export interface DispatchData {
  dispatch_status: "CERTIFIED_READY" | "ABORTED_SAFETY_LOCKOUT";
  certificate_id?: string;
  authorized_payload_hash?: string;
  timestamp: string;
  errors?: string[];
}

interface SubmissionDispatchStudioProps {
  data: DispatchData;
}

export const SubmissionDispatchStudio: React.FC<SubmissionDispatchStudioProps> = ({ data }) => {
  const isReady = data.dispatch_status === "CERTIFIED_READY";

  return (
    <div className={`rounded-lg shadow-2xl border mt-8 mb-16 animate-in fade-in duration-500 font-sans ${isReady ? 'bg-slate-900 border-emerald-700/50' : 'bg-slate-900 border-rose-700/50'}`}>
      <div className={`p-5 border-b flex flex-col md:flex-row justify-between items-start md:items-center ${isReady ? 'bg-emerald-950/20 border-emerald-900/30' : 'bg-rose-950/20 border-rose-900/30'}`}>
        <h3 className={`text-xl font-black flex items-center tracking-wide ${isReady ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isReady ? <ShieldCheck className="mr-3" size={26} /> : <ShieldAlert className="mr-3" size={26} />}
          Automated Submission Dispatch Gateway
        </h3>
        <div className={`flex items-center text-[10px] uppercase tracking-widest font-bold px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0 ${isReady ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-500/30' : 'bg-rose-900/40 text-rose-400 border border-rose-500/30'}`}>
          Status: {data.dispatch_status.replace(/_/g, ' ')}
        </div>
      </div>
      
      <div className="p-6">
        {/* Validation Gates */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700">
            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2">
              Pre-Flight Authorization Gates
            </h4>
            <ul className="space-y-3">
              <li className="flex items-center text-sm font-semibold text-slate-300">
                {isReady ? <CheckCircle2 size={16} className="text-emerald-400 mr-2" /> : <ShieldAlert size={16} className="text-rose-400 mr-2" />}
                Technical & Commercial Envelope Separation
              </li>
              <li className="flex items-center text-sm font-semibold text-slate-300">
                {isReady ? <CheckCircle2 size={16} className="text-emerald-400 mr-2" /> : <ShieldAlert size={16} className="text-rose-400 mr-2" />}
                Cryptographic Signature Validation
              </li>
              <li className="flex items-center text-sm font-semibold text-slate-300">
                {isReady ? <CheckCircle2 size={16} className="text-emerald-400 mr-2" /> : <ShieldAlert size={16} className="text-rose-400 mr-2" />}
                Bank Guarantee Validity Integrity
              </li>
            </ul>
          </div>

          <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700 flex flex-col justify-center items-center relative overflow-hidden">
             {/* Certificate Viewer */}
             {isReady ? (
               <div className="text-center z-10">
                 <FileKey size={48} className="text-emerald-400 mx-auto mb-3 opacity-80" />
                 <h4 className="text-sm font-black text-emerald-400 uppercase tracking-widest mb-1">Official Submission Certificate</h4>
                 <div className="font-mono text-xl font-bold text-slate-100 mb-2">{data.certificate_id}</div>
                 <div className="text-[10px] text-slate-500 font-mono break-all px-4">{data.authorized_payload_hash}</div>
               </div>
             ) : (
               <div className="text-center z-10">
                 <ShieldAlert size={48} className="text-rose-500 mx-auto mb-3 opacity-80" />
                 <h4 className="text-sm font-black text-rose-500 uppercase tracking-widest mb-1">Dispatch Lockout Triggered</h4>
                 <div className="text-xs text-rose-400 font-semibold px-4 mt-2">
                   {data.errors?.map((err, i) => <div key={i}>{err}</div>)}
                 </div>
               </div>
             )}
             
             {/* Subtle Animated Background for Ready state */}
             {isReady && <div className="absolute inset-0 bg-emerald-500/5 animate-pulse rounded-lg pointer-events-none"></div>}
          </div>
        </div>

        {/* Action Trigger */}
        <div className="flex justify-center mt-6 pt-6 border-t border-slate-800">
          <button 
            disabled={!isReady}
            className={`flex items-center text-sm uppercase tracking-widest font-black px-12 py-4 rounded shadow-xl transition-all ${
              isReady 
              ? 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer hover:scale-105' 
              : 'bg-slate-800 text-slate-500 cursor-not-allowed'
            }`}
          >
            <Send size={20} className="mr-3" /> 
            {isReady ? 'Execute Final Dispatch' : 'System Locked'}
          </button>
        </div>
        
      </div>
    </div>
  );
};
