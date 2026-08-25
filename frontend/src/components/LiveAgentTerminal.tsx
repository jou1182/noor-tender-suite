'use client';

import React, { useEffect, useRef } from 'react';
import { Terminal, Radio, CheckCircle2, Loader2, XCircle } from 'lucide-react';
import { AgentLogLine } from '../types/dashboard';

interface LiveAgentTerminalProps {
  logs: AgentLogLine[];
  connected: boolean;
}

export const LiveAgentTerminal: React.FC<LiveAgentTerminalProps> = ({ logs, connected }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs.length]);

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/60">
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
          <Terminal className="h-4 w-4 text-teal-400" />
          Multi-Agent Decision Stream
        </div>
        <span className={`inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border ${
          connected ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' : 'bg-amber-500/15 text-amber-300 border-amber-500/40'
        }`}>
          <Radio className={`h-3 w-3 ${connected ? 'animate-pulse' : ''}`} />
          {connected ? 'Live' : 'Reconnecting'}
        </span>
      </div>

      <div className="h-72 overflow-y-auto p-4 space-y-1.5 font-mono text-xs">
        {logs.length === 0 && (
          <p className="text-slate-600 italic">Awaiting agent telemetry — trigger an audit to begin streaming…</p>
        )}
        {logs.map((log) => (
          <div key={log.id} className="flex items-start gap-2">
            {log.status === 'completed' ? (
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
            ) : log.status === 'error' ? (
              <XCircle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
            ) : (
              <Loader2 className="h-3.5 w-3.5 text-cyan-400 animate-spin shrink-0 mt-0.5" />
            )}
            <div className="min-w-0">
              <p className="text-slate-300 leading-relaxed">
                <span className="text-teal-400 font-bold mr-1.5">[{log.agent}]</span>
                {log.message}
              </p>
              <p className="text-[10px] text-slate-600">{new Date(log.timestamp).toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
