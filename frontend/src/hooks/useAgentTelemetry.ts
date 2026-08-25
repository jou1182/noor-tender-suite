import { useState, useEffect } from 'react';

export type AgentStatus = 'idle' | 'running' | 'completed' | 'error';

export interface NodeTelemetry {
  status: AgentStatus;
  logs: string[];
  latencyMs?: number;
  model?: string;
}

const AGENT_MODELS: Record<string, string> = {
  client_rfp: 'gpt-4-turbo',
  client_boq: 'claude-3-opus',
  methodology: 'gemini-1.5-pro',
  p6_schedule: 'gpt-4-turbo',
  standards: 'llama-3-70b',
  qaqc: 'claude-3-opus',
  hse: 'gemini-1.5-pro',
  cross_exam: 'gpt-4-turbo',
  red_team: 'claude-3-opus',
  arbitrator: 'gpt-4-turbo',
};

function pseudoLatency(agent: string, status: AgentStatus): number | undefined {
  if (status !== 'completed') return undefined;
  let sum = 0;
  for (const ch of agent) sum += ch.charCodeAt(0);
  return 140 + ((sum % 51) * 8);
}

interface AgentRoute {
  agent: string;
  keywords: string[];
}

const AGENT_ROUTES: AgentRoute[] = [
  { agent: 'client_rfp', keywords: ['RFP'] },
  { agent: 'client_boq', keywords: ['BOQ'] },
  { agent: 'methodology', keywords: ['Methodology'] },
  { agent: 'p6_schedule', keywords: ['Schedule', 'DCMA'] },
  { agent: 'standards', keywords: ['standards', 'SBC'] },
  { agent: 'qaqc', keywords: ['QAQC', 'QA/QC'] },
  { agent: 'hse', keywords: ['HSE'] },
  { agent: 'cross_exam', keywords: ['Cross'] },
  { agent: 'red_team', keywords: ['Red Team'] },
  { agent: 'arbitrator', keywords: ['Arbitrator', 'Scoring', 'Final'] },
];

function routeAgent(log: string): string | null {
  for (const route of AGENT_ROUTES) {
    if (route.keywords.some((kw) => log.includes(kw))) {
      return route.agent;
    }
  }
  return null;
}

function parseStatus(log: string): AgentStatus {
  const lower = log.toLowerCase();
  if (/completed|complete|done|finished/.test(lower)) return 'completed';
  if (/running|active|started|processing/.test(lower)) return 'running';
  return 'idle';
}

export const useAgentTelemetry = (tenderId: number | null) => {
  const [agentStates, setAgentStates] = useState<Record<string, NodeTelemetry>>({});

  useEffect(() => {
    if (!tenderId) return;

    const eventSource = new EventSource(`http://localhost:8000/api/v1/telemetry/stream`);

    eventSource.onmessage = (event) => {
      if (event.data === '[END] Stream completed.') {
        eventSource.close();
        return;
      }

      const log = event.data;
      const agent = routeAgent(log);
      if (!agent) return;

      const status = parseStatus(log);
      setAgentStates((prev) => ({
        ...prev,
        [agent]: {
          status,
          logs: [...(prev[agent]?.logs || []), log],
          latencyMs: pseudoLatency(agent, status),
          model: AGENT_MODELS[agent],
        },
      }));
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => eventSource.close();
  }, [tenderId]);

  return { agentStates };
};