"use client";

import React, { useCallback, useEffect, useState } from 'react';
import { UploadCloud, X, FileText, FileSpreadsheet, FileCode, File, Loader2, AlertTriangle, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { triggerTenderAudit, AuditTriggerResult } from '../lib/api_client';
import { TenantContext } from '../lib/demoData';

const ACCEPTED_EXTENSIONS = ['.pdf', '.xlsx', '.xls', '.xer', '.ifc'] as const;
const ACCEPT_ATTR = '.pdf,.xlsx,.xls,.xer,.ifc';

const EXTENSION_META: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  '.pdf': { label: 'PDF', icon: FileText, color: 'text-red-500 bg-red-50' },
  '.xlsx': { label: 'XLSX', icon: FileSpreadsheet, color: 'text-emerald-600 bg-emerald-50' },
  '.xls': { label: 'XLS', icon: FileSpreadsheet, color: 'text-emerald-600 bg-emerald-50' },
  '.xer': { label: 'XER', icon: FileCode, color: 'text-blue-600 bg-blue-50' },
  '.ifc': { label: 'IFC', icon: FileCode, color: 'text-violet-600 bg-violet-50' },
};

const PROGRESS_PHASES = [
  'Uploading tender package...',
  'Authenticating workspace session...',
  'Dispatching LangGraph swarm...',
  'Waiting for agent telemetry...',
];

function getExtension(name: string): string {
  const idx = name.lastIndexOf('.');
  return idx >= 0 ? name.slice(idx).toLowerCase() : '';
}

function isAccepted(name: string): boolean {
  return (ACCEPTED_EXTENSIONS as readonly string[]).includes(getExtension(name));
}

interface UploadTenderModalProps {
  open: boolean;
  onClose: () => void;
  tenant: TenantContext;
  onSuccess: (result: AuditTriggerResult) => void;
}

export const UploadTenderModal: React.FC<UploadTenderModalProps> = ({ open, onClose, tenant, onSuccess }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState(false);

  useEffect(() => {
    if (open) {
      setFiles([]);
      setRejected([]);
      setError(null);
      setSubmitting(false);
      setPhaseIndex(0);
      setUploaded(false);
    }
  }, [open]);

  useEffect(() => {
    if (!submitting) return;
    const id = setInterval(() => setPhaseIndex((i) => Math.min(i + 1, PROGRESS_PHASES.length - 1)), 900);
    return () => clearInterval(id);
  }, [submitting]);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const list = Array.from(incoming);
    const accepted = list.filter((f) => isAccepted(f.name));
    const bad = list.filter((f) => !isAccepted(f.name)).map((f) => f.name);
    setFiles((prev) => [...prev, ...accepted]);
    setRejected((prev) => [...prev, ...bad]);
  }, []);

  const removeFile = useCallback((name: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== name));
  }, []);

  const submit = async () => {
    if (files.length === 0 || submitting) return;
    setSubmitting(true);
    setError(null);
    setPhaseIndex(0);
    try {
      const result = await triggerTenderAudit(files, tenant);
      setUploaded(true);
      onSuccess(result);
      window.dispatchEvent(new CustomEvent('tenders-changed', { detail: { tenderId: result.tender_id } }));
      setTimeout(onClose, 600);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Tender ingestion failed unexpectedly.');
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-900/70 backdrop-blur-sm" onClick={() => !submitting && onClose()} />
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-blue-600" />
              Upload Tender Package
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Multi-agent swarm ingestion — accepts PDF, XLSX, XER and IFC.
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={submitting}
            className="p-2 rounded-lg hover:bg-slate-200 text-slate-500 transition disabled:opacity-40"
            aria-label="Close upload modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="flex items-center gap-2 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
            <ShieldCheck className="h-4 w-4 shrink-0" />
            Authenticated workspace: {tenant.name} — demo JWT auto-injected on all audit requests.
          </div>

          <div
            className="w-full p-8 border-2 border-dashed border-slate-300 rounded-xl bg-slate-50 text-center transition hover:bg-slate-100 hover:border-blue-400 cursor-pointer"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files) addFiles(e.dataTransfer.files);
            }}
            onClick={() => document.getElementById('tender-package-input')?.click()}
          >
            <UploadCloud className="mx-auto h-10 w-10 text-slate-400" />
            <p className="mt-2 text-sm font-semibold text-slate-700">
              Drag & drop your tender package, or <span className="text-blue-600 underline">browse</span>
            </p>
            <div className="mt-3 flex flex-wrap justify-center gap-1.5">
              {(['PDF', 'XLSX', 'XER', 'IFC'] as const).map((tag) => (
                <span key={tag} className="text-[10px] font-bold uppercase tracking-wider bg-white border border-slate-200 rounded-md px-2 py-1 text-slate-600">
                  {tag}
                </span>
              ))}
            </div>
            <input
              id="tender-package-input"
              type="file"
              multiple
              accept={ACCEPT_ATTR}
              className="hidden"
              onChange={(e) => {
                if (e.target.files) addFiles(e.target.files);
                e.target.value = '';
              }}
            />
          </div>

          {rejected.length > 0 && (
            <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Skipped unsupported file(s): {rejected.join(', ')}. Only PDF, XLSX, XER and IFC are accepted.
            </div>
          )}

          {files.length > 0 && (
            <ul className="space-y-2 max-h-56 overflow-y-auto">
              {files.map((file) => {
                const ext = getExtension(file.name);
                const meta = EXTENSION_META[ext] || { label: 'FILE', icon: File, color: 'text-slate-500 bg-slate-100' };
                const Icon = meta.icon;
                return (
                  <li key={file.name} className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-3 py-2">
                    <span className={`h-9 w-9 rounded-lg flex items-center justify-center shrink-0 ${meta.color}`}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-800 truncate">{file.name}</p>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">{meta.label}</p>
                    </div>
                    <span className="text-xs text-slate-400 shrink-0">{(file.size / 1024).toFixed(0)} KB</span>
                    <button
                      onClick={() => removeFile(file.name)}
                      disabled={submitting}
                      className="p-1.5 rounded-md hover:bg-red-50 text-slate-400 hover:text-red-600 transition disabled:opacity-40"
                      aria-label={`Remove ${file.name}`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

          {submitting && (
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-blue-800">
                <Loader2 className="h-4 w-4 animate-spin shrink-0" />
                {uploaded ? 'Audit dispatched — swarm telemetry streaming...' : PROGRESS_PHASES[phaseIndex]}
              </div>
              <div className="mt-3 h-1.5 w-full bg-blue-100 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-teal-500 to-blue-600 rounded-full transition-all duration-700 animate-pulse"
                  style={{ width: `${((phaseIndex + 1) / PROGRESS_PHASES.length) * 100}%` }} />
              </div>
            </div>
          )}

          {uploaded && !submitting && (
            <div className="flex items-center gap-2 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              Tender ingested — the swarm canvas is streaming live agent telemetry.
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-lg px-3 py-2">
              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>
                <span className="font-bold">Ingestion failed: </span>
                {error}. The API returned an error — verify the backend and workspace token.
              </span>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2.5 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition disabled:opacity-40"
            >
              Cancel
            </button>
            <button
              onClick={submit}
              disabled={files.length === 0 || submitting}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-400 hover:to-blue-500 shadow-lg shadow-blue-500/20 transition disabled:opacity-40 disabled:shadow-none"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
              {submitting ? 'Ingesting...' : 'Run Full-Stack Audit'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};