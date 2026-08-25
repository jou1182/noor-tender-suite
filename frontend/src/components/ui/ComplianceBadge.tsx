'use client';

import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Ban } from 'lucide-react';
import { cn } from '../../lib/cn';

export type ComplianceTone = 'COMPLIANT' | 'DEVIATION' | 'NON_COMPLIANT' | 'BLOCKED';

interface ComplianceBadgeProps {
  status: string;
  tone?: ComplianceTone;
  className?: string;
}

const TONE_CONFIG: Record<ComplianceTone, { icon: React.ElementType; cls: string }> = {
  COMPLIANT: { icon: CheckCircle2, cls: 'bg-compliance-green/15 text-compliance-green border-compliance-green/40' },
  DEVIATION: { icon: AlertTriangle, cls: 'bg-warning-amber/15 text-warning-amber border-warning-amber/40' },
  NON_COMPLIANT: { icon: XCircle, cls: 'bg-risk-red/15 text-risk-red border-risk-red/40' },
  BLOCKED: { icon: Ban, cls: 'bg-risk-red/15 text-risk-red border-risk-red/40' },
};

/** Normalize any backend status string to a ComplianceTone. */
export function normalizeTone(status: string): ComplianceTone {
  const upper = status.toUpperCase();
  if (upper.includes('COMPLIANT') && upper.includes('DEVIATION')) return 'DEVIATION';
  if (upper.includes('COMPLIANT') || upper === 'PASS') return 'COMPLIANT';
  if (upper.includes('NON_COMPLIANT') || upper.includes('FAIL') || upper === 'CRITICAL_GAP') return 'NON_COMPLIANT';
  if (upper.includes('BLOCK')) return 'BLOCKED';
  return 'DEVIATION';
}

/** Reusable compliance status pill with semantic colors. */
export const ComplianceBadge: React.FC<ComplianceBadgeProps> = ({ status, tone, className }) => {
  const resolved = tone ?? normalizeTone(status);
  const cfg = TONE_CONFIG[resolved];
  const Icon = cfg.icon;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-full border',
        cfg.cls,
        className,
      )}
    >
      <Icon className="h-3 w-3" />
      {status}
    </span>
  );
};
