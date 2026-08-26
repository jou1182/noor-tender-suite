"use client";

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  FolderSearch, UploadCloud, FileText, Loader2, MapPin, Pin,
  Search, CheckCircle, XCircle, FileWarning, Boxes, Database, Trash2, CheckCircle2,
  ClipboardCheck, TrendingUp, AlertTriangle, RefreshCw,
} from 'lucide-react';
import type { RagCitation, TenderDocumentItem } from '../types/platform';
import { t, getLang, type Lang } from '../lib/i18n';

const API = 'http://localhost:8000';

const CATEGORY_META: Record<string, { label: string; cls: string }> = {
  EVALUATION_CRITERIA: { label: 'Evaluation Criteria', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/40' },
  SPECIFICATIONS: { label: 'Specifications', cls: 'bg-blue-500/15 text-blue-300 border-blue-500/40' },
  BOQ: { label: 'BOQ', cls: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40' },
  DRAWINGS: { label: 'Drawings / CAD', cls: 'bg-violet-500/15 text-violet-300 border-violet-500/40' },
  FORMS: { label: 'Forms', cls: 'bg-sky-500/15 text-sky-300 border-sky-500/40' },
  ADDENDUM: { label: 'Addendum', cls: 'bg-orange-500/15 text-orange-300 border-orange-500/40' },
  CONTRACT: { label: 'Contract', cls: 'bg-teal-500/15 text-teal-300 border-teal-500/40' },
  PROPOSAL: { label: '⭐ Our Proposal', cls: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/40' },
  OTHER: { label: 'Other', cls: 'bg-slate-500/15 text-slate-300 border-slate-500/40' },
};

const STATUS_META: Record<string, { icon: React.ElementType; cls: string }> = {
  PROCESSED: { icon: CheckCircle, cls: 'text-emerald-400' },
  PROCESSING: { icon: Loader2, cls: 'text-cyan-400 animate-spin' },
  FAILED: { icon: XCircle, cls: 'text-rose-400' },
  REGISTERED: { icon: FileText, cls: 'text-slate-400' },
};

/** نتيجة تقييم العرض الفني */
interface ProposalEval {
  score: number;
  addressed: number;
  total: number;
  summary: string;
  strengths: Array<{ clause_id: string; section: string; similarity: number }>;
  weaknesses: Array<{ clause_id: string; description: string; penalty_points: number }>;
  partial_coverage: Array<{ clause_id: string; similarity: number }>;
}

const STATUS_LABEL_KEY: Record<string, Parameters<typeof t>[0]> = {
  PROCESSED: 'statusProcessed', PROCESSING: 'statusProcessing',
  REGISTERED: 'statusRegistered', FAILED: 'statusFailed',
};

interface UploadState {
  name: string;
  progress: number;   // 0-100 (نسبة البايتات المرسلة)
  phase: 'uploading' | 'queued';
}

export const DocumentLibrary: React.FC<{ tenderId: number }> = ({ tenderId }) => {
  const [documents, setDocuments] = useState<TenderDocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploads, setUploads] = useState<Record<string, UploadState>>({});
  const [proposalUploading, setProposalUploading] = useState(false);
  const [scanFolder, setScanFolder] = useState('');
  const [scanBusy, setScanBusy] = useState(false);
  const [showScan, setShowScan] = useState(false);
  const [pinned, setPinned] = useState<number | null>(null);
  const [question, setQuestion] = useState('');
  const [citations, setCitations] = useState<RagCitation[]>([]);
  const [asking, setAsking] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [evaluation, setEvaluation] = useState<ProposalEval | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [evalError, setEvalError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const proposalInput = useRef<HTMLInputElement>(null);
  const [lang, setLang] = useState<Lang>('ar');
  useEffect(() => {
    setLang(getLang());
    const onChange = (e: Event) => setLang((e as CustomEvent).detail as Lang);
    window.addEventListener('contech.lang-changed', onChange);
    return () => window.removeEventListener('contech.lang-changed', onChange);
  }, []);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/v1/documents?tender_id=${tenderId}`);
      const data = await res.json();
      setDocuments(data.documents || []);
      const pinnedDoc = (data.documents || []).find((d: TenderDocumentItem) => d.is_pinned_criteria);
      setPinned(pinnedDoc ? pinnedDoc.id : null);
      return data.documents as TenderDocumentItem[];
    } finally {
      setLoading(false);
    }
  }, [tenderId]);

  useEffect(() => { load(); }, [load]);

  // استطلاع دوري طالما هناك ملفات قيد المعالجة (المعالجة الآن في الخلفية)
  useEffect(() => {
    const anyProcessing = documents.some((d) => d.status === 'PROCESSING' || d.status === 'REGISTERED');
    if (!anyProcessing) return;
    const t = setInterval(() => load(), 2500);
    return () => clearInterval(t);
  }, [documents, load]);

  /** رفع متوازٍ مع تتبع تقدم لكل ملف — دفعات من 3 لتفادي إغراق الخادم */
  const uploadFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const list = Array.from(files);

    const uploadOne = (file: File) => new Promise<void>((resolve) => {
      const form = new FormData();
      form.append('file', file);
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API}/api/v1/documents/upload?tender_id=${tenderId}&ocr_enabled=true`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          setUploads((prev) => ({ ...prev, [file.name]: { name: file.name, progress: pct, phase: 'uploading' } }));
        }
      };
      xhr.onload = () => {
        setUploads((prev) => ({ ...prev, [file.name]: { name: file.name, progress: 100, phase: 'queued' } }));
        resolve();
      };
      xhr.onerror = () => resolve();
      xhr.send(form);
    });

    // دفعات متوازية (3 في نفس الوقت)
    for (let i = 0; i < list.length; i += 3) {
      await Promise.all(list.slice(i, i + 3).map(uploadOne));
    }
    // نظّف قائمة التقدم بعد استقرار قصير
    setTimeout(() => setUploads({}), 1500);
    await load();
    if (fileInput.current) fileInput.current.value = '';
  };

  /** رفع العرض الفني بفئة إجبارية PROPOSAL — لا اعتماد على التصنيف التلقائي */
  const uploadProposal = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const list = Array.from(files);
    setProposalUploading(true);
    try {
      for (const file of list) {
        const form = new FormData();
        form.append('file', file);
        try {
          await fetch(`${API}/api/v1/documents/upload?tender_id=${tenderId}&doc_category=PROPOSAL`, {
            method: 'POST', body: form,
          });
        } catch { /* continue */ }
      }
      await load();
    } finally {
      setProposalUploading(false);
      if (proposalInput.current) proposalInput.current.value = '';
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

  /** تقييم العرض الفني ضد معايير المنافسة */
  const evaluateProposal = async () => {
    setEvaluating(true);
    setEvalError('');
    setEvaluation(null);
    try {
      const res = await fetch(`${API}/api/v1/proposal-evaluation/evaluate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tender_id: tenderId }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setEvaluation(data);
    } catch (e) {
      setEvalError(e instanceof Error ? e.message : 'فشل التقييم');
    } finally {
      setEvaluating(false);
    }
  };

  const processed = documents.filter((d) => d.status === 'PROCESSED').length;
  const criteriaFound = documents.filter((d) => d.doc_category === 'EVALUATION_CRITERIA').length;
  const proposalDocs = documents.filter((d) => d.doc_category === 'PROPOSAL');
  const processingCount = documents.filter((d) => d.status === 'PROCESSING' || d.status === 'REGISTERED').length;

  return (
    <div className="rounded-lg shadow-2xl border bg-slate-900 border-slate-700 p-5 space-y-5 text-slate-100">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <span className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shrink-0">
            <Boxes className="h-4 w-4 text-white" />
          </span>
          <div>
            <h2 className="text-lg font-black text-white leading-tight">{t("documentLibrary", lang)}</h2>
            <p className="text-xs text-slate-400">
              <span className="font-mono font-bold text-teal-300">{documents.length}</span> {t("files", lang)} ·
              <span className="font-mono font-bold text-emerald-300"> {processed}</span> {t("processed", lang)} ·
              <span className="font-mono font-bold text-amber-300"> {criteriaFound}</span> {t("criteria", lang)} ·
              <span className="font-mono font-bold text-fuchsia-300"> {proposalDocs.length}</span> {t("proposal", lang)}
              {processingCount > 0 && (
                <span className="text-cyan-300"> · {processingCount} {t("processingBg", lang)}</span>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => setShowScan(!showScan)}
            title={t("scanServerHint", lang)}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-2 rounded-lg border border-slate-600 text-slate-200 hover:bg-slate-800 transition">
            <FolderSearch className="h-4 w-4" /> {t("scanServerFolder", lang)}
          </button>
          {/* رفع إضافي — يضيف للقائمة دون مسح الموجود */}
          {/* زر مخصص للعرض الفني — يضمن التصنيف PROPOSAL 100% */}
          <button onClick={() => proposalInput.current?.click()}
            title={t("uploadProposalHint", lang)}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white shadow hover:from-fuchsia-500 hover:to-purple-500 transition disabled:opacity-50">
            <ClipboardCheck className="h-4 w-4" />
            {t("uploadProposal", lang)}
          </button>
          <input ref={proposalInput} type="file" multiple hidden
            accept=".pdf,.docx,.doc"
            onChange={(e) => uploadProposal(e.target.files)} />
          <button onClick={() => fileInput.current?.click()}
            title={t("uploadFilesHint", lang)}
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow disabled:opacity-50">
            <UploadCloud className="h-4 w-4" />
            {t("uploadFiles", lang)}
          </button>
          <input ref={fileInput} type="file" multiple hidden
            accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv,.dxf,.dwg,.zip"
            onChange={(e) => uploadFiles(e.target.files)} />
        </div>
      </div>

      {/* أشرطة تقدم الرفع */}
      {Object.keys(uploads).length > 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-950/60 p-3 space-y-2">
          {Object.values(uploads).map((u) => (
            <div key={u.name} className="flex items-center gap-2">
              <FileText className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              <span className="text-xs text-slate-300 truncate flex-1 max-w-[300px]">{u.name}</span>
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden min-w-[80px]">
                <div className="h-full bg-gradient-to-r from-teal-500 to-blue-500 rounded-full transition-all"
                  style={{ width: `${u.progress}%` }} />
              </div>
              <span className="text-[10px] font-mono text-slate-500 w-16 text-right">
                {u.phase === 'queued' ? 'queued ✓' : `${u.progress}%`}
              </span>
            </div>
          ))}
        </div>
      )}

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

      {/* لوحة تقييم العرض الفني */}
      {(proposalDocs.length > 0 || evaluation) && (
        <div className="rounded-lg border border-fuchsia-500/40 bg-fuchsia-500/5 p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <p className="text-[11px] font-black uppercase tracking-widest text-fuchsia-300 flex items-center gap-1.5">
              <ClipboardCheck className="h-4 w-4" />
              {t("proposalEvalTitle", lang)}
              {proposalDocs.length > 0 && (
                <span className="normal-case text-slate-400">({proposalDocs.length} {t("proposal", lang)})</span>
              )}
            </p>
            <button onClick={evaluateProposal} disabled={evaluating || processed === 0}
              title={t("proposalEvalHint", lang) || ""}
              className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white shadow disabled:opacity-40 transition">
              {evaluating ? <Loader2 className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
              {t("evaluateProposal", lang)}
            </button>
          </div>

          {evalError && (
            <p className="text-xs text-rose-300 font-semibold" dir="auto">⚠ {evalError}</p>
          )}

          {evaluation && (
            <div className="space-y-3">
              {/* الدرجة */}
              <div className="flex items-center gap-4 flex-wrap">
                <div className={`text-4xl font-black font-mono ${
                  evaluation.score >= 80 ? 'text-emerald-400' : evaluation.score >= 50 ? 'text-amber-400' : 'text-rose-400'
                }`}>
                  {evaluation.score}
                  <span className="text-base text-slate-500">/100</span>
                </div>
                <div className="text-xs text-slate-400 leading-relaxed" dir="rtl">
                  <p>البنود المجابة: <span className="text-white font-bold">{evaluation.addressed}/{evaluation.total}</span></p>
                  <p className="text-slate-500">{evaluation.summary}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {/* نقاط القوة */}
                <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-3">
                  <p className="text-[10px] font-black uppercase tracking-widest text-emerald-300 mb-2 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5" /> {t("strengths", lang)} ({evaluation.strengths.length})
                  </p>
                  {evaluation.strengths.length === 0 ? (
                    <p className="text-xs text-slate-500">{t("noFull", lang)}</p>
                  ) : (
                    <ul className="space-y-1.5">
                      {evaluation.strengths.map((s) => (
                        <li key={s.clause_id} className="text-xs text-slate-300 flex items-start gap-1.5">
                          <CheckCircle2 className="h-3 w-3 text-emerald-400 mt-0.5 shrink-0" />
                          <span><span className="font-mono text-emerald-300">{s.clause_id}</span> — {s.section}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* نقاط الضعف */}
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/5 p-3">
                  <p className="text-[10px] font-black uppercase tracking-widest text-rose-300 mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5" /> {t("weaknesses", lang)} ({evaluation.weaknesses.length})
                  </p>
                  {evaluation.weaknesses.length === 0 ? (
                    <p className="text-xs text-emerald-400">{t("noGaps", lang)}</p>
                  ) : (
                    <ul className="space-y-1.5">
                      {evaluation.weaknesses.map((w) => (
                        <li key={w.clause_id} className="text-xs text-slate-300 flex items-start gap-1.5" dir="rtl">
                          <XCircle className="h-3 w-3 text-rose-400 mt-0.5 shrink-0" />
                          <span>
                            <span className="font-mono text-rose-300">{w.clause_id}</span>
                            <span className="text-slate-400"> (-{w.penalty_points} نقطة)</span> — {w.description}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* تغطية جزئية */}
              {evaluation.partial_coverage.length > 0 && (
                <p className="text-xs text-amber-300/80" dir="rtl">
                  ⚡ {t("partialCoverage", lang)}: {evaluation.partial_coverage.map((p) => p.clause_id).join('، ')}
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="space-y-2">{[0, 1, 2].map((i) => <div key={i} className="h-12 rounded-lg bg-slate-800/60 animate-pulse" />)}</div>
      ) : documents.length === 0 ? (
        <div className="border-2 border-dashed border-slate-700 rounded-xl p-10 text-center">
          <UploadCloud className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <p className="text-sm font-bold text-slate-300">{t("noDocs", lang)}</p>
<p className="text-xs text-slate-500 mt-1">{t("noDocsHint", lang)}</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-950/60">
              <tr>
                <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">{t("files", lang)}</th>
                <th className="px-3 py-2.5 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest w-44">{t("criteria", lang)}</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-28">{t("processed", lang)}</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-28">/</th>
                <th className="px-3 py-2.5 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest w-44">{t("catEvaluation", lang)}</th>
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
                          <p className="font-semibold text-slate-100 truncate max-w-[280px]" dir="auto">{doc.filename}</p>
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
                        <StatusIcon className="h-3.5 w-3.5" /> {t(STATUS_LABEL_KEY[doc.status] || 'statusRegistered', lang)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-center font-mono text-xs text-slate-400">
                      {doc.page_count || '—'} / {doc.text_chars ? `${(doc.text_chars / 1000).toFixed(0)}k` : '—'}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        {pinned === doc.id ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-black uppercase text-amber-300">
                            <Pin className="h-3.5 w-3.5" /> {t("pinnedGate", lang)}
                          </span>
                        ) : (
                          <button onClick={() => pinCriteria(doc.id)}
                            title="ثبّت هذه الوثيقة كمعيار تقييم ملزم للمنافسة"
                            className="inline-flex items-center gap-1 text-[10px] font-black uppercase tracking-wider px-2.5 py-1 rounded-lg border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 transition">
                            <MapPin className="h-3 w-3" /> {t("pinAction", lang)}
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
          <Search className="h-3.5 w-3.5" /> {t("askCorpus", lang)}
        </p>
        <div className="flex gap-2">
          <input value={question} onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && ask()}
            placeholder={t("askPlaceholder", lang)}
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
