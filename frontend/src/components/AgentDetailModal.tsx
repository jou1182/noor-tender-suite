import React from 'react';
import { X, Activity } from 'lucide-react';

export interface NodeData {
  label?: string;
  status?: string;
  logs?: string[];
  [key: string]: unknown;
}

interface AgentDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodeData: NodeData | null;
}

const STATUS_STYLES: Record<string, string> = {
  completed: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/50',
  running: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/50 animate-pulse',
  error: 'bg-rose-500/15 text-rose-300 border-rose-500/50',
  idle: 'bg-slate-800/80 text-slate-400 border-slate-700',
};

export const AgentDetailModal: React.FC<AgentDetailModalProps> = ({ isOpen, onClose, nodeData }) => {
  if (!isOpen || !nodeData) return null;

  const status = nodeData.status || 'idle';

  return (
    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 rounded-xl">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-md p-6 m-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-black text-slate-100 tracking-wide">{nodeData.label}</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-800 rounded-lg transition text-slate-400 hover:text-white">
            <X size={18} />
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Execution Status</h3>
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-black rounded-full border ${STATUS_STYLES[status] || STATUS_STYLES.idle}`}>
              <Activity size={12} />
              {status.toUpperCase()}
            </span>
          </div>
          <div>
            <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Live Telemetry Logs</h3>
            <div className="bg-black/50 border border-slate-800 text-emerald-400 text-xs font-mono p-3 rounded-lg h-40 overflow-y-auto">
              {nodeData.logs && nodeData.logs.length > 0 ? (
                nodeData.logs.map((log: string, idx: number) => (
                  <div key={idx} className="py-0.5 break-words">{log}</div>
                ))
              ) : (
                <div className="text-slate-600">Waiting for telemetry...</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};