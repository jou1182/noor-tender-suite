import React from 'react';
import { Blocks, Link, ShieldCheck, ServerCrash, Hash } from 'lucide-react';

export interface BlockTransaction {
  event_type: string;
  [key: string]: any;
}

export interface BlockchainData {
  block_height: number;
  merkle_root: string;
  block_hash: string;
  previous_hash: string;
  transactions: BlockTransaction[];
  ledger_integrity_verified: boolean;
  timestamp: number;
}

interface BlockchainLedgerStudioProps {
  data: BlockchainData;
}

export const BlockchainLedgerStudio: React.FC<BlockchainLedgerStudioProps> = ({ data }) => {
  const isVerified = data.ledger_integrity_verified;

  return (
    <div className={`rounded-lg shadow-2xl border mt-8 mb-16 animate-in fade-in duration-500 font-sans ${isVerified ? 'bg-slate-900 border-indigo-700/50' : 'bg-slate-900 border-rose-700/50'}`}>
      <div className={`p-5 border-b flex flex-col md:flex-row justify-between items-start md:items-center ${isVerified ? 'bg-indigo-950/20 border-indigo-900/30' : 'bg-rose-950/20 border-rose-900/30'}`}>
        <h3 className={`text-xl font-black flex items-center tracking-wide ${isVerified ? 'text-indigo-400' : 'text-rose-400'}`}>
          <Blocks className="mr-3" size={26} />
          Enterprise Blockchain Audit Ledger
        </h3>
        <div className={`flex items-center text-[10px] uppercase tracking-widest font-bold px-3 py-1.5 rounded-full shadow-sm mt-3 md:mt-0 ${isVerified ? 'bg-indigo-900/40 text-indigo-400 border border-indigo-500/30' : 'bg-rose-900/40 text-rose-400 border border-rose-500/30'}`}>
          {isVerified ? <ShieldCheck size={14} className="mr-1.5" /> : <ServerCrash size={14} className="mr-1.5" />}
          {isVerified ? 'Ledger Intact & Cryptographically Verified' : 'CRITICAL: Block Chain Compromised'}
        </div>
      </div>
      
      <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Block Explorer Metadata */}
        <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700 h-full">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2 flex items-center">
             <Hash size={14} className="mr-2 text-indigo-400" /> Genesis Block Metadata
          </h4>
          
          <div className="space-y-4">
             <div>
               <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider mb-1">Block Height (Index)</span>
               <div className="text-2xl font-black text-slate-200">{data.block_height}</div>
             </div>
             
             <div>
               <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider mb-1">Merkle Root Signature</span>
               <div className="text-xs font-mono font-bold text-emerald-400 bg-slate-900/50 p-2 rounded border border-emerald-900/30 break-all">
                 {data.merkle_root}
               </div>
             </div>
             
             <div>
               <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider mb-1 flex items-center">
                 <Link size={12} className="mr-1" /> Previous Block Hash
               </span>
               <div className="text-[10px] font-mono text-slate-400 bg-slate-900/30 p-2 rounded border border-slate-700/50 break-all">
                 {data.previous_hash}
               </div>
             </div>
             
             <div>
               <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider mb-1">Current Block Hash</span>
               <div className="text-[10px] font-mono text-blue-400 bg-slate-900/30 p-2 rounded border border-blue-900/30 break-all">
                 {data.block_hash}
               </div>
             </div>
          </div>
        </div>

        {/* Transaction Matrix */}
        <div className="bg-slate-800/80 p-5 rounded-lg border border-slate-700 h-full">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 border-b border-slate-700 pb-2 flex items-center">
             <Blocks size={14} className="mr-2 text-blue-400" /> Anchored Transactions ({data.transactions.length})
          </h4>
          
          <div className="space-y-3 overflow-y-auto max-h-[300px] pr-2">
            {data.transactions.map((tx, idx) => (
              <div key={idx} className="bg-slate-900/80 p-3 rounded border border-slate-700/50 text-xs">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-bold text-indigo-300 tracking-wider uppercase text-[10px]">{tx.event_type}</span>
                </div>
                <div className="grid grid-cols-1 gap-1">
                  {Object.entries(tx).filter(([k]) => k !== 'event_type').map(([key, val]) => (
                    <div key={key} className="flex justify-between border-t border-slate-800 pt-1">
                      <span className="text-slate-500 capitalize">{key.replace('_', ' ')}</span>
                      <span className="font-mono text-slate-300 truncate max-w-[200px]" title={String(val)}>
                        {typeof val === 'number' ? (key === 'timestamp' ? new Date(val * 1000).toISOString() : val) : String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
        
      </div>
    </div>
  );
};
