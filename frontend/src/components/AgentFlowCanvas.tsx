"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { ReactFlow, Background, BackgroundVariant, Controls, MarkerType, Node, Edge, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  FileSearch, Table, BookOpen, CalendarClock, ShieldCheck, ClipboardCheck,
  HardHat, Swords, ShieldAlert, Gavel, Activity, CheckCircle2, Timer, Cpu,
} from 'lucide-react';
import { AgentDetailModal, NodeData } from './AgentDetailModal';
import { useAgentTelemetry } from '../hooks/useAgentTelemetry';
import type { AgentStatus } from '../hooks/useAgentTelemetry';

const API = 'http://localhost:8000';

export interface AgentMeta {
  id: string;
  label: string;
  agentName: string;
  role: string;
  icon: React.ElementType;
  avatarClass: string;
  avatarEmoji: string;
}

/**
 * الهيكل الثابت للوحة (المواقع والأيقونات) — لكن الأسماء والأدوار والصور
 * تُدمج من سجل الوكلاء الحي (/api/v1/agents) حتى تنعكس إعادة التسمية فوراً.
 */
export const AGENT_METAS: AgentMeta[] = [
  { id: 'client_rfp', label: 'Client RFP Agent', agentName: 'Aria', role: 'RFP Clause Extraction', icon: FileSearch, avatarClass: 'from-rose-500 to-orange-500', avatarEmoji: '👁️' },
  { id: 'client_boq', label: 'Client BOQ Agent', agentName: 'Bo', role: 'Bill of Quantities Parsing', icon: Table, avatarClass: 'from-amber-500 to-yellow-500', avatarEmoji: '📊' },
  { id: 'methodology', label: 'Methodology Agent', agentName: 'Mika', role: 'Method Statement Audit', icon: BookOpen, avatarClass: 'from-violet-500 to-purple-500', avatarEmoji: '🧠' },
  { id: 'p6_schedule', label: 'P6 Schedule Agent', agentName: 'Daan', role: 'DCMA 14-Point & Monte Carlo', icon: CalendarClock, avatarClass: 'from-sky-500 to-cyan-500', avatarEmoji: '🗓️' },
  { id: 'standards', label: 'Standards Agent', agentName: 'Sami', role: 'SBC Requirement Mapping', icon: ShieldCheck, avatarClass: 'from-emerald-500 to-teal-500', avatarEmoji: '📚' },
  { id: 'qaqc', label: 'QA/QC Agent', agentName: 'Qira', role: 'ITP Inspection Register', icon: ClipboardCheck, avatarClass: 'from-blue-500 to-indigo-500', avatarEmoji: '🔬' },
  { id: 'hse', label: 'HSE Agent', agentName: 'Hadi', role: 'HIRA Risk Matrix', icon: HardHat, avatarClass: 'from-orange-500 to-amber-600', avatarEmoji: '🦺' },
  { id: 'cross_exam', label: 'Cross-Exam Agent', agentName: 'Xena', role: 'Adversarial Validation', icon: Swords, avatarClass: 'from-fuchsia-500 to-pink-500', avatarEmoji: '⚔️' },
  { id: 'red_team', label: 'Red Team Agent', agentName: 'Rhea', role: 'Vulnerability Probing', icon: ShieldAlert, avatarClass: 'from-red-500 to-rose-600', avatarEmoji: '🔥' },
  { id: 'arbitrator', label: 'Arbitrator Agent', agentName: 'Amir', role: 'Final Score Synthesis', icon: Gavel, avatarClass: 'from-slate-500 to-gray-600', avatarEmoji: '⚖️' },
];

const STATUS_STYLES: Record<AgentStatus, { border: string; chip: string; dot: string; label: string; pulse?: boolean }> = {
  idle: { border: 'border-slate-700', chip: 'bg-slate-800/80 text-slate-400 border-slate-700', dot: 'bg-slate-500', label: 'IDLE' },
  running: {
    border: 'border-cyan-500 shadow-[0_0_22px_rgba(34,211,238,0.45)]',
    chip: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/50',
    dot: 'bg-cyan-400',
    label: 'RUNNING',
    pulse: true,
  },
  completed: {
    border: 'border-emerald-500 shadow-[0_0_18px_rgba(16,185,129,0.35)]',
    chip: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/50',
    dot: 'bg-emerald-400',
    label: 'COMPLETED',
  },
  error: { border: 'border-rose-500 shadow-[0_0_18px_rgba(244,63,94,0.35)]', chip: 'bg-rose-500/15 text-rose-300 border-rose-500/50', dot: 'bg-rose-400', label: 'ERROR' },
};

interface AgentNodeData extends NodeData {
  meta: AgentMeta;
  status: AgentStatus;
  logs: string[];
  latencyMs?: number;
  model?: string;
}

const AgentAvatar: React.FC<{ meta: AgentMeta; status: AgentStatus }> = ({ meta, status }) => (
  <div className="relative shrink-0">
    <div className={`h-12 w-12 rounded-full bg-gradient-to-br ${meta.avatarClass} flex items-center justify-center shadow-lg ring-2 ring-white/10`}>
      <svg viewBox="0 0 24 24" className="h-7 w-7 text-white/90" fill="currentColor" aria-hidden="true">
        <circle cx="12" cy="8" r="4" />
        <path d="M4.5 21c.6-4.2 3.7-6.5 7.5-6.5s6.9 2.3 7.5 6.5" />
      </svg>
    </div>
    <span className={`absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-slate-900 ${STATUS_STYLES[status].dot} ${status === 'running' ? 'animate-pulse' : ''}`} />
  </div>
);

const AgentNode: React.FC<{ data: AgentNodeData }> = ({ data }) => {
  const { meta, status, logs, latencyMs, model } = data;
  const style = STATUS_STYLES[status] || STATUS_STYLES.idle;
  const Icon = meta.icon;
  const lastLog = logs && logs.length > 0 ? logs[logs.length - 1] : null;

  return (
    <div className={`min-w-[220px] w-[230px] rounded-xl border bg-slate-900/85 backdrop-blur-md transition-all duration-300 ${style.border}`}>
      <Handle type="target" position={Position.Left} className="!bg-slate-600 !border-0 !h-2 !w-2" />
      <Handle type="source" position={Position.Right} className="!bg-slate-600 !border-0 !h-2 !w-2" />

      <div className="flex items-start gap-3 p-3">
        <AgentAvatar meta={meta} status={status} />
        <div className="min-w-0 flex-1">
          <span className="block whitespace-nowrap text-xs font-black text-slate-100 tracking-wide">{meta.label}</span>
          <div className="mt-1 flex items-center justify-between gap-1">
            <span className="flex items-center gap-1 text-[11px] font-bold text-cyan-400/90 min-w-0">
              <Icon className="h-3 w-3 shrink-0" />
              <span className="truncate">{meta.agentName}</span>
            </span>
            <span className={`flex items-center gap-1 text-[8px] font-black uppercase tracking-widest rounded-full border px-1.5 py-0.5 whitespace-nowrap shrink-0 ${style.chip} ${style.pulse ? 'animate-pulse' : ''}`}>
              <span className={`h-1 w-1 rounded-full ${style.dot}`} />
              {style.label}
            </span>
          </div>
          <div className="text-[9px] font-semibold uppercase tracking-wider text-slate-500 truncate">{meta.role}</div>
          {status !== 'idle' && (
            <div className="mt-1 flex items-center justify-between gap-1 font-mono text-[8px] text-slate-500">
              <span className="flex items-center gap-1">
                <Timer className="h-2.5 w-2.5 text-slate-600" />
                {latencyMs ? `${latencyMs}ms` : '—'}
              </span>
              <span className="flex items-center gap-1 truncate">
                <Cpu className="h-2.5 w-2.5 text-slate-600 shrink-0" />
                {model || '—'}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="mx-3 mb-2.5 rounded-md border border-slate-800 bg-black/40 px-2 py-1.5">
        {lastLog ? (
          <p className="truncate font-mono text-[9px] leading-relaxed text-slate-400">{lastLog.replace(/^\[[^\]]*\]\s*/, '')}</p>
        ) : (
          <p className="flex items-center gap-1 font-mono text-[9px] text-slate-600">
            <Activity className="h-2.5 w-2.5" /> waiting for telemetry...
          </p>
        )}
      </div>
    </div>
  );
};

const nodeTypes = { agent: AgentNode };

const INITIAL_POSITIONS: Record<string, { x: number; y: number }> = {
  client_rfp: { x: 20, y: 40 },
  methodology: { x: 285, y: 40 },
  standards: { x: 550, y: 40 },
  hse: { x: 815, y: 40 },
  red_team: { x: 1080, y: 40 },
  client_boq: { x: 20, y: 250 },
  p6_schedule: { x: 285, y: 250 },
  qaqc: { x: 550, y: 250 },
  cross_exam: { x: 815, y: 250 },
  arbitrator: { x: 1080, y: 250 },
};

const EDGE_ROUTES: Array<{ id: string; source: string; target: string }> = [
  { id: 'e1', source: 'client_rfp', target: 'client_boq' },
  { id: 'e2', source: 'client_boq', target: 'methodology' },
  { id: 'e3', source: 'methodology', target: 'p6_schedule' },
  { id: 'e4', source: 'p6_schedule', target: 'standards' },
  { id: 'e5', source: 'standards', target: 'qaqc' },
  { id: 'e6', source: 'qaqc', target: 'hse' },
  { id: 'e7', source: 'hse', target: 'cross_exam' },
  { id: 'e8', source: 'cross_exam', target: 'red_team' },
  { id: 'e9', source: 'red_team', target: 'arbitrator' },
];

export const AgentFlowCanvas = ({ tenderId }: { tenderId: number | null }) => {
  const { agentStates } = useAgentTelemetry(tenderId);
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [registryMeta, setRegistryMeta] = useState<Record<string, { name_en: string; name_ar: string; role: string; avatar_emoji: string }>>({});

  // دمج هوية الوكلاء من السجل الحي — إعادة التسمية في /settings تنعكس هنا فوراً
  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/api/v1/agents`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!cancelled && data?.agents) {
          const map: typeof registryMeta = {};
          for (const a of data.agents as Array<{ key: string; name_en: string; name_ar: string; role: string; avatar_emoji: string }>) {
            map[a.key] = { name_en: a.name_en, name_ar: a.name_ar, role: a.role, avatar_emoji: a.avatar_emoji };
          }
          setRegistryMeta(map);
        }
      })
      .catch(() => { /* اللوحة تعمل بالهوية الافتراضية عند غياب الخادم */ });
    return () => { cancelled = true; };
  }, []);

  const nodes: Node[] = useMemo(() => {
    return AGENT_METAS.map((meta) => {
      const live = registryMeta[meta.id];
      const resolved: AgentMeta = live
        ? {
            ...meta,
            label: `${meta.label} · ${live.name_en}`,
            agentName: `${live.name_en} (${live.name_ar})`,
            role: live.role || meta.role,
            avatarEmoji: live.avatar_emoji || meta.avatarEmoji,
          }
        : meta;
      const state = agentStates[meta.id] || { status: 'idle', logs: [] };
      return {
        id: meta.id,
        type: 'agent',
        position: INITIAL_POSITIONS[meta.id] || { x: 0, y: 0 },
        data: { meta: resolved, status: state.status, logs: state.logs, latencyMs: state.latencyMs, model: state.model, label: resolved.label } as AgentNodeData,
      };
    });
  }, [agentStates, registryMeta]);

  const edges: Edge[] = useMemo(() => {
    return EDGE_ROUTES.map((route) => {
      const sourceState = agentStates[route.source]?.status || 'idle';
      const active = sourceState === 'running';
      const done = sourceState === 'completed';
      const color = active ? '#22d3ee' : done ? '#10b981' : '#334155';
      return {
        ...route,
        type: 'smoothstep',
        animated: active || done,
        markerEnd: { type: MarkerType.ArrowClosed, color, width: 14, height: 14 },
        style: { stroke: color, strokeWidth: active ? 2 : 1.5, opacity: done ? 0.95 : 0.75 },
      };
    });
  }, [agentStates]);

  return (
    <div className="h-[620px] w-full rounded-xl bg-slate-950 overflow-hidden relative border border-slate-800">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.4}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => {
          const data = node.data as AgentNodeData;
          setSelectedNode({ label: data.label, status: data.status, logs: data.logs });
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1.4} color="#1e293b" />
        <Controls className="!bg-slate-900 !border-slate-700 [&>button]:!bg-slate-800 [&>button]:!border-slate-700 [&>button]:!text-slate-300" />
      </ReactFlow>
      <div className="pointer-events-none absolute left-3 top-3 z-10 flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 backdrop-blur">
        <Activity className="h-3 w-3 text-cyan-400" />
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">
          Live Swarm — {Object.values(agentStates).filter((s) => s.status === 'completed').length}/10
        </span>
        <CheckCircle2 className="h-3 w-3 text-emerald-400" />
      </div>
      <AgentDetailModal
        isOpen={!!selectedNode}
        onClose={() => setSelectedNode(null)}
        nodeData={selectedNode}
      />
    </div>
  );
};