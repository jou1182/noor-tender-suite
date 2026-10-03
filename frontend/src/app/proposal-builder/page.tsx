"use client";

/**
 * مولد العروض الفنية — صفحة عربية لتوليد العرض الفني Word
 * عبر وحدة ATPAS المدمجة (/api/v1/atpas).
 * الرحلة: نوع المشروع ← الجهة المالكة ← الأكواد ← توليد وتحميل.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowRight, Building2, CheckSquare, Download, FileText, Hammer,
  Loader2, Square, Sun, Wrench,
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

interface ProjectInfo { name_ar: string; name_en: string; networks: string[] }
interface OwnerInfo { owner_id: string; name_ar: string; name_en: string; network: string; mandatory_codes_count: number }
interface CodeInfo { code_id: string; activity_name_ar: string; activity_name_en: string; category: string; sequence_order: number; dependencies: string[] }
interface CompanyInfo { company_name_ar: string; product_name_ar: string; publisher_ar: string }

const CATEGORY_LABEL: Record<string, string> = {
  '001': 'الأعمال التمهيدية',
  '002': 'أعمال الحفر والردم',
  '003': 'الأعمال الرئيسية',
  '004': 'الأعمال الثانوية',
  '005': 'الأعمال الختامية',
};

export default function ProposalBuilderPage() {
  const router = useRouter();
  const [company, setCompany] = useState<CompanyInfo | null>(null);
  const [projects, setProjects] = useState<Record<string, ProjectInfo>>({});
  const [owners, setOwners] = useState<Record<string, OwnerInfo>>({});
  const [codes, setCodes] = useState<CodeInfo[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  const [ownerId, setOwnerId] = useState<string>('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loadingCodes, setLoadingCodes] = useState(false);
  const [building, setBuilding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const load = useCallback(async (path: string) => {
    const r = await fetch(`${API}${path}`);
    if (!r.ok) throw new Error(`${path} → ${r.status}`);
    return r.json();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [c, p, o] = await Promise.all([
          load('/api/v1/atpas/company'),
          load('/api/v1/atpas/projects'),
          load('/api/v1/atpas/owners'),
        ]);
        setCompany(c); setProjects(p); setOwners(o);
      } catch (e) {
        setError('تعذر الاتصال بخادم المنظومة — شغّل الخادم الخلفي أولاً (uvicorn app.main:app --port 8000)');
      }
    })();
  }, [load]);

  useEffect(() => {
    if (!projectId) { setCodes([]); setSelected(new Set()); return; }
    setLoadingCodes(true); setError(null); setDone(null);
    load(`/api/v1/atpas/codes?project_id=${projectId}`)
      .then((list: CodeInfo[]) => { setCodes(list); setSelected(new Set()); })
      .catch(() => setError('تعذر تحميل الأكواد لهذا المشروع'))
      .finally(() => setLoadingCodes(false));
  }, [projectId, load]);

  const toggle = (codeId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(codeId)) next.delete(codeId); else next.add(codeId);
      return next;
    });
  };

  const grouped = useMemo(() => {
    const g = new Map<string, CodeInfo[]>();
    codes.forEach((c) => {
      const cat = c.category || '000';
      if (!g.has(cat)) g.set(cat, []);
      g.get(cat)!.push(c);
    });
    return [...g.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [codes]);

  const selectAll = () => setSelected(new Set(codes.map((c) => c.code_id)));
  const clearAll = () => setSelected(new Set());

  const build = async () => {
    setBuilding(true); setError(null); setDone(null);
    try {
      const r = await fetch(`${API}/api/v1/atpas/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, owner_id: ownerId, selected_codes: [...selected] }),
      });
      if (!r.ok) {
        const detail = await r.json().catch(() => ({}));
        throw new Error(detail.detail || `فشل التوليد (${r.status})`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${projectId}_${ownerId}_proposal.docx`;
      a.click();
      URL.revokeObjectURL(url);
      setDone(`تم توليد العرض الفني بنجاح — ${selected.size} كوداً في المستند`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'فشل التوليد');
    } finally {
      setBuilding(false);
    }
  };

  return (
    <main dir="rtl" className="min-h-screen bg-slate-950 text-white" style={{ fontFamily: 'var(--font-tajawal), Tajawal, sans-serif' }}>
      {/* الشريط العلوي */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/')} className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition" aria-label="رجوع">
              <ArrowRight className="h-5 w-5" />
            </button>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-teal-400 to-blue-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <FileText className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-base font-black tracking-tight">مولد العروض الفنية</h1>
              <p className="text-[10px] uppercase tracking-widest text-teal-400 font-bold">
                {company ? company.company_name_ar : '…'} — ATPAS Engine
              </p>
            </div>
          </div>
          <span className="hidden sm:flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-slate-400 border border-slate-700 rounded-full px-3 py-1.5">
            <Sun size={10} className="text-amber-400" /> منظومة النور
          </span>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {error && (
          <div className="rounded-xl border border-rose-500/50 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div>
        )}
        {done && (
          <div className="rounded-xl border border-emerald-500/50 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200 flex items-center gap-2">
            <CheckSquare className="h-4 w-4 shrink-0" /> {done}
          </div>
        )}

        {/* الخطوة 1: نوع المشروع */}
        <section>
          <h2 className="flex items-center gap-2 text-sm font-black text-slate-300 mb-3">
            <span className="h-6 w-6 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs">1</span>
            اختر نوع المشروع
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(projects).map(([pid, p]) => (
              <button
                key={pid}
                onClick={() => { setProjectId(pid); setOwnerId(''); }}
                className={`rounded-xl border px-4 py-4 text-right transition ${
                  projectId === pid
                    ? 'border-teal-400 bg-teal-500/10 shadow-lg shadow-teal-500/10'
                    : 'border-slate-700 bg-slate-900 hover:border-slate-500'
                }`}
              >
                <Hammer className={`h-5 w-5 mb-2 ${projectId === pid ? 'text-teal-300' : 'text-slate-500'}`} />
                <p className="font-bold text-sm">{p.name_ar}</p>
                <p className="text-[10px] text-slate-500 mt-1" dir="ltr">{pid}</p>
              </button>
            ))}
          </div>
        </section>

        {/* الخطوة 2: الجهة المالكة */}
        <section className={projectId ? '' : 'opacity-40 pointer-events-none'}>
          <h2 className="flex items-center gap-2 text-sm font-black text-slate-300 mb-3">
            <span className="h-6 w-6 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs">2</span>
            اختر الجهة المالكة
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(owners).map(([oid, o]) => (
              <button
                key={oid}
                onClick={() => setOwnerId(oid)}
                className={`rounded-xl border px-3 py-3 text-right transition ${
                  ownerId === oid
                    ? 'border-blue-400 bg-blue-500/10'
                    : 'border-slate-700 bg-slate-900 hover:border-slate-500'
                }`}
              >
                <Building2 className={`h-4 w-4 mb-1.5 ${ownerId === oid ? 'text-blue-300' : 'text-slate-500'}`} />
                <p className="font-bold text-xs leading-tight">{o.name_ar}</p>
                {o.mandatory_codes_count > 0 && (
                  <p className="text-[9px] text-slate-500 mt-1">{o.mandatory_codes_count} كود إلزامي</p>
                )}
              </button>
            ))}
          </div>
        </section>

        {/* الخطوة 3: الأكواد */}
        <section className={projectId ? '' : 'opacity-40 pointer-events-none'}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="flex items-center gap-2 text-sm font-black text-slate-300">
              <span className="h-6 w-6 rounded-lg bg-teal-500/20 text-teal-300 flex items-center justify-center text-xs">3</span>
              اختر الأكواد الفنية
              <span className="text-teal-400 text-xs font-bold">({selected.size} / {codes.length})</span>
            </h2>
            <div className="flex gap-2">
              <button onClick={selectAll} className="text-[11px] font-bold text-teal-300 border border-teal-500/40 rounded-lg px-3 py-1.5 hover:bg-teal-500/10 transition">تحديد الكل</button>
              <button onClick={clearAll} className="text-[11px] font-bold text-slate-400 border border-slate-600 rounded-lg px-3 py-1.5 hover:bg-slate-800 transition">مسح</button>
            </div>
          </div>

          {loadingCodes && (
            <div className="flex items-center justify-center py-12 text-slate-400">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          )}

          {!loadingCodes && codes.length === 0 && projectId && (
            <p className="text-sm text-slate-500 py-8 text-center">لا توجد أكواد نشطة لهذا المشروع.</p>
          )}

          <div className="space-y-4">
            {grouped.map(([cat, list]) => (
              <div key={cat} className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center gap-2">
                  <Wrench className="h-3.5 w-3.5 text-teal-400" />
                  <span className="text-xs font-black text-slate-300">{CATEGORY_LABEL[cat] || `الفئة ${cat}`}</span>
                  <span className="text-[10px] text-slate-500">({list.length})</span>
                </div>
                <div className="divide-y divide-slate-800/60">
                  {list.map((c) => {
                    const on = selected.has(c.code_id);
                    return (
                      <button
                        key={c.code_id}
                        onClick={() => toggle(c.code_id)}
                        className={`w-full flex items-center gap-3 px-4 py-2.5 text-right transition ${on ? 'bg-teal-500/5' : 'hover:bg-slate-800/40'}`}
                      >
                        {on ? (
                          <CheckSquare className="h-4 w-4 text-teal-400 shrink-0" />
                        ) : (
                          <Square className="h-4 w-4 text-slate-600 shrink-0" />
                        )}
                        <span className="text-[10px] font-mono text-slate-500 w-24 shrink-0" dir="ltr">{c.code_id}</span>
                        <span className={`text-xs flex-1 ${on ? 'text-white font-semibold' : 'text-slate-300'}`}>{c.activity_name_ar}</span>
                        {c.dependencies.length > 0 && (
                          <span className="text-[9px] text-amber-400/80 shrink-0" title={`يعتمد على: ${c.dependencies.join(', ')}`}>
                            يعتمد على {c.dependencies.length}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* زر التوليد */}
        <div className="sticky bottom-4">
          <button
            onClick={build}
            disabled={!projectId || !ownerId || selected.size === 0 || building}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-blue-600 text-white font-black text-sm px-6 py-4 rounded-xl shadow-xl shadow-teal-500/20 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {building ? <Loader2 className="h-5 w-5 animate-spin" /> : <Download className="h-5 w-5" />}
            {building ? 'جارٍ توليد العرض الفني…' : `توليد العرض الفني وتحميله (${selected.size} كوداً)`}
          </button>
          {!ownerId && projectId && selected.size > 0 && (
            <p className="text-center text-[11px] text-amber-300/80 mt-2">اختر الجهة المالكة أولاً لتحديد نمط التنسيق</p>
          )}
        </div>
      </div>
    </main>
  );
}
