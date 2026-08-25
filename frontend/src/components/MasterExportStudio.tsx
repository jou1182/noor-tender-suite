import React from 'react';
import { Lock, FileText, Download, ShieldCheck, CheckCircle2, FileWarning } from 'lucide-react';

export interface SignatureManifest {
  timestamp: string;
  master_hash: string;
  signatures: Record<string, string>;
}

export interface DossierData {
  dossier_status: string;
  sections_compiled: string[];
  manifest: SignatureManifest;
}

interface Props {
  data: DossierData | null;
}

export const MasterExportStudio: React.FC<Props> = ({ data }) => {
  if (!data) return null;

  const formatHash = (hash: string) => {
    if (hash === "MISSING") return "MISSING - SECTION NOT GENERATED";
    return `${hash.substring(0, 12)}.................................${hash.substring(hash.length - 12)}`;
  };

  return (
    <div className="bg-slate-900 rounded-lg shadow-2xl border-2 border-emerald-500/30 mt-8 mb-16 animate-in fade-in slide-in-from-bottom-8 duration-700 overflow-hidden text-slate-100 font-sans relative">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-indigo-500"></div>
      
      <div className="bg-black/40 p-5 border-b border-slate-700 flex flex-col md:flex-row justify-between items-start md:items-center">
        <h3 className="text-xl font-black flex items-center text-emerald-400 tracking-wide">
          <Lock className="mr-3" size={26} />
          Master Technical Proposal & Cryptographic Sealer
        </h3>
        <div className="flex items-center text-[10px] uppercase tracking-widest font-bold bg-emerald-900/40 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0">
          <ShieldCheck size={14} className="mr-1.5" /> Immutable SHA-256 Integration
        </div>
      </div>
      
      <div className="p-6">
        
        {/* Master Hash Banner */}
        <div className="bg-slate-800/90 border border-emerald-500/20 p-6 rounded-lg mb-8 shadow-inner flex flex-col xl:flex-row justify-between items-center relative overflow-hidden">
          <div className="absolute top-0 right-0 p-12 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none transform translate-x-1/2 -translate-y-1/2"></div>
          
          <div className="z-10 w-full">
            <h4 className="text-[10px] font-bold text-emerald-500/80 uppercase tracking-widest mb-2 flex items-center">
              <ShieldCheck size={14} className="mr-1.5" /> Master Dossier Cryptographic Signature
            </h4>
            <div className="text-xl md:text-2xl font-mono font-black text-emerald-400 tracking-tighter select-all break-all">
              {data.manifest.master_hash}
            </div>
            <div className="text-xs text-slate-400 font-mono mt-2">Certified Assembly Timestamp: {data.manifest.timestamp}</div>
          </div>
          
          <button className="z-10 mt-6 xl:mt-0 w-full xl:w-auto flex items-center justify-center bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-4 rounded-lg font-bold transition-all shadow-lg hover:shadow-emerald-500/20 active:scale-95 shrink-0 whitespace-nowrap">
            <Download size={20} className="mr-2" /> Download Secured Master Dossier
          </button>
        </div>

        {/* Sections Breakdown */}
        <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2 flex items-center">
          <FileText size={14} className="mr-2 text-slate-400" /> Compiled Document Manifest Tracing
        </h4>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Object.entries(data.manifest.signatures).map(([section, hash], idx) => {
            const isMissing = hash === "MISSING";
            
            return (
              <div key={idx} className={`p-4 rounded-lg border flex flex-col justify-between shadow-sm transition-colors ${
                isMissing ? 'bg-slate-900/50 border-slate-700/50' : 'bg-slate-800/60 border-slate-600 hover:border-slate-500 hover:bg-slate-800/90'
              }`}>
                <div className="flex justify-between items-start mb-3">
                  <span className={`text-sm font-bold capitalize tracking-wide ${isMissing ? 'text-slate-500' : 'text-slate-200'}`}>
                    {section.replace(/_/g, ' ')}
                  </span>
                  {isMissing ? (
                    <FileWarning size={16} className="text-slate-600" />
                  ) : (
                    <CheckCircle2 size={16} className="text-emerald-500" />
                  )}
                </div>
                <div className="bg-black/40 p-2 rounded flex items-center border border-slate-700/50">
                  <Lock size={12} className={`mr-2 shrink-0 ${isMissing ? 'text-slate-700' : 'text-slate-500'}`} />
                  <span className={`text-[10px] font-mono select-all ${isMissing ? 'text-slate-600 italic' : 'text-slate-400 tracking-tight'}`}>
                    {formatHash(hash)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
        
      </div>
    </div>
  );
};
