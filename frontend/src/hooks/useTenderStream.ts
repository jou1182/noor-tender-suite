'use client';

import { useEffect, useRef, useState } from 'react';
import { AgentLogLine, TenderStreamEvent } from '../types/dashboard';

const SSE_BASE = 'http://localhost:8000';

export interface UseTenderStreamResult {
  events: TenderStreamEvent[];
  logs: AgentLogLine[];
  connected: boolean;
  error: string | null;
}

/**
 * EventSource/SSE consumer for `/api/v1/projects/{id}/stream`.
 * Maintains a real-time agent decision stream for LiveAgentTerminal.
 */
export function useTenderStream(projectId: string | null): UseTenderStreamResult {
  const [events, setEvents] = useState<TenderStreamEvent[]>([]);
  const [logs, setLogs] = useState<AgentLogLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const source = new EventSource(`${SSE_BASE}/api/v1/projects/${projectId}/stream`);

    source.onopen = () => setConnected(true);
    source.onerror = () => {
      setConnected(false);
      setError('Stream disconnected — retrying…');
      source.close();
    };

    // Named event: structured payloads (e.g. agent.completed, compliance.update).
    source.addEventListener('message', (ev) => {
      try {
        const data = JSON.parse((ev as MessageEvent).data) as TenderStreamEvent;
        setEvents((prev) => [...prev.slice(-200), data]);
      } catch {
        /* non-JSON keep-alive */
      }
    });

    // Fallback: default onmessage for `data:` frames.
    source.onmessage = (ev) => {
      if (ev.data === '[END] Stream completed.') {
        source.close();
        setConnected(false);
        return;
      }
      const line = toLogLine(ev.data);
      if (line) setLogs((prev) => [...prev.slice(-500), line]);
    };

    esRef.current = source;
    return () => {
      source.close();
      esRef.current = null;
    };
  }, [projectId]);

  return { events, logs, connected, error };
}

function toLogLine(raw: string): AgentLogLine | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    agent: inferAgent(trimmed),
    message: trimmed,
    status: /completed|complete|done|finished/i.test(trimmed) ? 'completed' : /running|processing|auditing/i.test(trimmed) ? 'running' : 'running',
    timestamp: new Date().toISOString(),
  };
}

function inferAgent(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes('sbc') || lower.includes('compliance')) return 'SBC-304 Auditor';
  if (lower.includes('ve') || lower.includes('value engineering')) return 'VE Optimizer';
  if (lower.includes('boq')) return 'BOQ Parser';
  if (lower.includes('spec') || lower.includes('pdf')) return 'Spec Parser';
  if (lower.includes('method') || lower.includes('schedule')) return 'Methodology Auditor';
  if (lower.includes('risk')) return 'Risk Mitigation';
  return 'Cross-Exam Agent';
}
