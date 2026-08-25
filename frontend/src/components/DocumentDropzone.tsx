'use client';

import React, { useCallback, useState } from 'react';
import { UploadCloud, FileSpreadsheet, FileText, X, CheckCircle2, Loader2 } from 'lucide-react';
import { WorkspaceDocument } from '../types/dashboard';

interface DocumentDropzoneProps {
  onUpload?: (files: File[]) => void;
}

const ACCEPTED = '.xlsx,.xls,.pdf';

export const DocumentDropzone: React.FC<DocumentDropzoneProps> = ({ onUpload }) => {
  const [dragging, setDragging] = useState(false);
  const [docs, setDocs] = useState<WorkspaceDocument[]>([]);
  const [processing, setProcessing] = useState(false);

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      const list = Array.from(files);
      if (list.length === 0) return;
      setProcessing(true);
      onUpload?.(list);

      const added: WorkspaceDocument[] = list.map((f, i) => ({
        id: `${Date.now()}-${i}`,
        filename: f.name,
        document_type: f.name.toLowerCase().endsWith('.pdf') ? 'spec' : 'boq',
        status: 'parsing',
        uploaded_at: new Date().toISOString(),
      }));
      setDocs((prev) => [...prev, ...added]);

      // Simulate parse completion for the demo (real flow via /stream).
      setTimeout(() => {
        setDocs((prev) => prev.map((d) => ({ ...d, status: 'parsed' as const })));
        setProcessing(false);
      }, 1800);
    },
    [onUpload],
  );

  const removeDoc = (id: string) => setDocs((prev) => prev.filter((d) => d.id !== id));

  return (
    <div className="space-y-4">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition ${
          dragging ? 'border-teal-400 bg-teal-500/5' : 'border-slate-700 bg-slate-950/40 hover:border-slate-500'
        }`}
      >
        <UploadCloud className={`h-10 w-10 mx-auto mb-3 ${dragging ? 'text-teal-400' : 'text-slate-500'}`} />
        <p className="text-sm font-bold text-slate-200">Drag &amp; drop tender documents</p>
        <p className="text-xs text-slate-500 mt-1">BOQ.xlsx (bill of quantities) and Spec.pdf (technical specifications)</p>
        <label className="inline-flex items-center gap-2 mt-4 text-xs font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-teal-500/15 text-teal-300 border border-teal-500/40 hover:bg-teal-500/25 cursor-pointer transition">
          Browse Files
          <input
            type="file"
            multiple
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => e.target.files && addFiles(e.target.files)}
          />
        </label>
      </div>

      {docs.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Ingested Documents ({docs.length})</span>
            {processing && <Loader2 className="h-4 w-4 text-teal-400 animate-spin" />}
          </div>
          <div className="divide-y divide-slate-800">
            {docs.map((d) => (
              <div key={d.id} className="flex items-center gap-3 px-4 py-3">
                {d.document_type === 'boq'
                  ? <FileSpreadsheet className="h-5 w-5 text-emerald-400 shrink-0" />
                  : <FileText className="h-5 w-5 text-rose-400 shrink-0" />}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-200 truncate">{d.filename}</p>
                  <p className="text-[10px] uppercase tracking-widest text-slate-500">{d.document_type} · {d.status}</p>
                </div>
                {d.status === 'parsed' ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                ) : (
                  <Loader2 className="h-4 w-4 text-teal-400 animate-spin shrink-0" />
                )}
                <button onClick={() => removeDoc(d.id)} className="text-slate-600 hover:text-rose-400 transition">
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
