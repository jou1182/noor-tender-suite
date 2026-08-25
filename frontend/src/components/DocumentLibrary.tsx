"use client";

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  FolderSearch, UploadCloud, FileText, Loader2, MapPin, Pin,
  Search, CheckCircle, XCircle, FileWarning, Boxes, Database, Trash2, CheckCircle2,
} from 'lucide-react';
import type { RagCitation, TenderDocumentItem } from '../types/platform';

const API = 'http://localhost:8000';

const CATEGORY_META: Record<string, { label: string; cls: string }> = {
  EVALUATION_CRITERIA: { label: 'Evaluation Criteria', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/40' },
  SPECIFICATIONS: { label: 'Specifications', cls: 'bg-blue-500/15 text-blue-300 border-blue-500/40' },
  BOQ: { label: 'BOQ', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
  DRAWINGS: { label: 'Drawings / CAD', cls: 'bg-violet-500/15 text-violet-300 border-violet-500/40' },
  FORMS: { label: 'Forms', cls: 'bg-sky-500/15 text-sky-300 border-sky-500/40' },
  ADDENDUM: { label: 'Addendum', cls: 'bg-orange-500/15 text-orange-300 border-orange-500/40' },
  CONTRACT: { label: 'Contract', cls: 'bg-teal-500/15 text-teal-300 border-teal-500/40' },
  OTHER: { label: 'Other', cls: 'bg-slate-500/15 text-slate-300 border-slate-500/40' },
};

const STATUS_META: Record<string, { icon: React.ElementType; cls: string }> = {
  PROCESSED: { icon: CheckCircle, cls: 'text-emerald-400' },
  PROCESSING: { icon: Loader2, cls: 'text-cyan-400 animate-spin' },
  FAILED: { icon: XCircle, cls: 'text-rose-400' },
  REGISTERED: { icon: FileText, cls: 'text-slate-400' },
};

export const DocumentLibrary: React.FC<{ tenderId: number }> = ({ tenderId }) => {
  const [documents, setDocuments] = useState<TenderDocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [scanFolder, setScanFolder] = useState('');
  const [scanBusy, setScanBusy] = useState(false);
  const [showScan, setShowScan] = useState(false);
  const [pinned, setPinned] = useState<number | null>(null);
  const [question, setQuestion] = useState('');
  const [citations, setCitations] = useState<RagCitation[]>([]);
  const [asking, setAsking] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/documents?tender_id=${tenderId}`);
      const data = await res.json();
      setDocuments(data.documents || []);
      const pinnedDoc = (data.documents || []).find((d: TenderDocumentItem) => d.is_pinned_criteria);
      setPinned(pinnedDoc ? pinnedDoc.id : null);
    } finally {
      setLoading(false);
    }
  }, [tenderId]);

  useEffect(() => { load(); }, [load]);

  const uploadFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        const form = new FormData();
        form.append('file', file);
        try {
          await fetch(`${API}/api/v1/documents/upload?tender_id=${tenderId}&ocr_enabled=true`, {
            method: 'POST', body: form,
          });
        } catch { /* continue with remaining files */ }
      }
      await load();
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = '';
    }
  };

  const scanServerFolder = async () => {
    if (!scanFolder) return;
    setScanBusy(true);
    try {
      await fetch(`${API}/api/v1/documents/scan-folder`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tender_id: tenderId, folder: scanFolder }),
      });
      setShowScan(false);
      setScanFolder('');
      await load();
    } finally {
      setScanBusy(false);
    }
  };

  const pinCriteria = async (docId: number) => {
    await fetch(`${API}/api/v1/documents/criteria/pin`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tender_id: tenderId, document_id: docId }),
    });
    setPinned(docId);
    await load();
  };

  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);

  const deleteDoc = async (docId: number) => {
    setDeleting(docId);
    try {
      await fetch(`${API}/api/v1/documents/${docId}`, { method: 'DELETE' });
      setConfirmDeleteId(null);
      await load();
    } finally {
      setDeleting(null);
    }
  };

  const ask = async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const res = await fetch(`${API}/api/v1/documents/ask`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tender_id: tenderId, question }),
      });
      const data = await res.json();
      setCitations(data.citations || []);
    } finally {
      setAsking(false);
    }
  };

  const processed = documents.filter((d) => d.status === 'PROCESSED').length;
  const criteriaFound = documents.filter((d) => d.doc_category === 'EVALUATION_CRITERIA').length;

  return (
    <div className="rounded-lg shadow-2xl border bg-slate-900 border-slate-700 p-5 space-y-5 text-slate-100">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shrink-0">
            <Boxes className="h-4 w-4 text-white" />
          </span>
          <div>
            <h2 className="text-lg font-black text-white leading-tight">Document Library &amp; Ingestion</h2>
            <p className="text-xs text-slate-400">
              <span className="font-mono font-bold text-teal-300">{documents.length}</span> files ·
              <span className="font-mono font-bold text-emerald-300"> {processed}</span> processed ·
              <span className="font-mono font-bold text-amber-300"> {criteriaFound}</span> criteria candidates
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowScan(!showScan)}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-2 rounded-lg border border-slate-600 text-slate-200 hover:bg-slate-800 transition">
            <FolderSearch className="h-4 w-4" /> Scan Server Folder
          </button>
          <button onClick={() => fileInput.current?.click()} disabled={uploading}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow disabled:opacity-50">
            {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
            {uploading ? 'Uploading…' : 'Upload Files'}
          </button>
          <input ref={fileInput} type="file" multiple hidden
            accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv,.dxf,.dwg,.zip"
            onChange={(e) => uploadFiles(e.target.files)} />
        </div>
      </div>

      {showScan && (
        <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4 flex flex-col md:flex-row gap-3 items-stretch">
          <input value={scanFolder} onChange={(e) => setScanFolder(e.target.value)}
            placeholder="Server folder path, e.g. D:\Tenders\RFP_2026"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-teal-500" />
          <button onClick={scanServerFolder} disabled={scanBusy || !scanFolder}
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-blue-600 disabled:opacity-40">
            {scanBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FolderSearch className="h-4 w-4" />}
            Scan &amp; Register
          </button>
        </div>
      )}

      {loading ? (
        <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="h-12 rounded-lg bg-slate-800/60 animate-pulse" />)}</div>
      ) : documents.length === 0 ? (
        <div className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center">
          <UploadCloud className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-300">No documents ingested yet for this tender.</p>
          <p className="text-xs text-slate-500 mt-1">
            Upload the owner&apos;s RFP package (PDF / DOCX / XLSX / DXF / DWG) or scan a server folder — files bind to the active workspace.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-950/60">
              <tr>
                <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Document</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest w-44">Category</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-24">Status</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-28">Pages / Chars</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-44">Criteria Gate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70 bg-slate-900/40">
              {documents.map((doc) => {
                const status = STATUS_META[doc.status] || STATUS_META.REGISTERED;
                const StatusIcon = status.icon;
                const cat = CATEGORY_META[doc.doc_category] || CATEGORY_META.OTHER;
                const sizeMb = (doc.size_bytes / (1024 * 1024)).toFixed(1);
                return (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-3 py-2.5">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-500 shrink-0" />
                        <div className="min-w-0">
                          <p className="font-semibold text-slate-100 truncate max-w-[280px]">{doc.filename}</p>
                          <p className="text-[10px] text-slate-500 font-mono">{sizeMb} MB{doc.ocr_used ? ' · OCR' : ''}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className={`inline-block text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded-full border ${cat.cls}`}>
                        {cat.label}
                      </span>
                      <div className="mt-1 h-1 w-24 bg-slate-800 rounded-full overflow-hidden">
                        <div className="h-full bg-teal-500/80 rounded-full" style={{ width: `${Math.round(doc.classification_confidence * 100)}%` }} />
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <span className={`inline-flex items-center gap-1 text-[10px] font-black uppercase ${status.cls}`}>
                        <StatusIcon className="h-3.5 w-3.5" /> {doc.status}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-center font-mono text-xs text-slate-400">
                      {doc.page_count || '—'} / {doc.text_chars ? `${(doc.text_chars / 1000).toFixed(0)}k` : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {pinned === doc.id ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase text-amber-300">
                            <Pin className="h-3.5 w-3.5" /> Pinned Gate
                          </span>
                        ) : (
                          <button onClick={() => pinCriteria(doc.id)}
                            title="Pin as THE binding evaluation-criteria document"
                            className="inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-lg border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 transition">
                            <MapPin className="h-3 w-3" /> Pin
                          </button>
                        )}
                        {confirmDeleteId === doc.id ? (
                          <div className="flex items-center gap-1">
                            <button onClick={() => deleteDoc(doc.id)} disabled={deleting === doc.id}
                              title="تأكيد الحذف النهائي (النصوص والمتجهات والملف)"
                              className="p-1 rounded bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-50">
                              {deleting === doc.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3" />}
                            </button>
                            <button onClick={() => setConfirmDeleteId(null)}
                              className="p-1 rounded text-slate-400 hover:text-white"><XCircle className="h-3 w-3" /></button>
                          </div>
                        ) : (
                          <button onClick={() => setConfirmDeleteId(doc.id)}
                            title="حذف هذا المستند نهائياً من المكتبة"
                            className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition">
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* RAG ask */}
      <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-4">
        <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-2 flex items-center gap-1.5">
          <Search className="h-3.5 w-3.5" /> Ask the RFP Corpus — answers cite file &amp; page
        </p>
        <div className="flex gap-2">
          <input value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask()}
            placeholder="e.g. أين شرط الخرسانة المسلحة؟ / Where is the dewatering requirement?"
            dir="auto"
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500" />
          <button onClick={ask} disabled={asking || !question.trim()}
            className="px-4 py-2 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-blue-600 disabled:opacity-40">
            {asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
          </button>
        </div>
        {citations.length > 0 && (
          <div className="mt-3 space-y-2">
            {citations.map((c, i) => (
              <div key={i} className="rounded-lg border border-slate-700 bg-slate-900 p-3">
                <p className="text-[10px] font-black uppercase tracking-wider text-teal-300 flex items-center gap-1.5">
                  <FileWarning className="h-3 w-3" /> {c.filename} · page {c.page} · score {c.score}
                </p>
                <p className="text-xs text-slate-300 mt-1 leading-relaxed" dir="auto">{c.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
