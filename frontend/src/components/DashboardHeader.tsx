"use client";

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Boxes, Building2, ChevronDown, UploadCloud, Menu, X, ShieldCheck, Radio,
  Settings, Plus, Trash2, RefreshCw, Loader2, Check, RotateCcw, Languages, PenLine, FileText,
} from 'lucide-react';
import { TenderSummary, listTenders, createTender, deleteTender, renameTender } from '../lib/tenders_client';
import type { TenantContext } from '../lib/demoData';
import { t, getLang, setLang, type Lang } from '../lib/i18n';

interface DashboardHeaderProps {
  tenant: TenantContext;
  onTenantChange: (tenant: TenantContext) => void;
  onUploadClick: () => void;
  onNewCompetition: () => void;
}

/** سياق الهوية يُبنى الآن ديناميكياً من المنافسات الحقيقية في قاعدة البيانات. */
export const tenantFromTender = (t: TenderSummary): TenantContext => ({
  id: String(t.id),
  name: t.client_name || t.title,
  project: t.title,
  phase: t.status === 'completed' ? 'Completed' : t.status === 'processing' ? 'Swarm Running' : 'Draft',
  role: 'Lead Architect',
});

const PHASE_STYLE: Record<string, string> = {
  Draft: 'text-slate-300 border-slate-500/40 bg-slate-500/15',
  'Swarm Running': 'text-cyan-300 border-cyan-500/40 bg-cyan-500/15',
  Completed: 'text-emerald-300 border-emerald-500/40 bg-emerald-500/15',
};

export const DashboardHeader: React.FC<DashboardHeaderProps> = ({ tenant, onTenantChange, onUploadClick, onNewCompetition }) => {
  const router = useRouter();
  const [tenants, setTenants] = useState<TenderSummary[]>([]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newClient, setNewClient] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameTitle, setRenameTitle] = useState('');
  const [renameClient, setRenameClient] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [lang, setLangState] = useState<Lang>('ar');
  const menuRef = useRef<HTMLDivElement>(null);

  // تحميل اللغة المحفوظة + الاستماع لتبديلها
  useEffect(() => {
    setLangState(getLang());
    const onChange = (e: Event) => setLangState((e as CustomEvent).detail as Lang);
    window.addEventListener('noor.lang-changed', onChange);
    return () => window.removeEventListener('noor.lang-changed', onChange);
  }, []);

  const toggleLang = () => {
    const next: Lang = lang === 'ar' ? 'en' : 'ar';
    setLang(next);
    setLangState(next);
  };

  const load = useCallback(async () => {
    try {
      const list = await listTenders();
      setTenants(list);
      return list;
    } catch {
      return [];
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // استرجاع المنافسة النشطة من جلسة المتصفح (sessionStorage):
  // - تحديث الصفحة: يبقى سياقك
  // - إغلاق المتصفح وفتحه: جلسة جديدة نظيفة تبدأ من أول منافسة
  // - القائمة نفسها (كل المشاريع) تبقى دائماً من قاعدة البيانات
  useEffect(() => {
    if (loadingList) return;
    // بعد «بدء من جديد» (tenant.id='') نبقى في وضع فارغ — لا اختيار تلقائي
    if (tenant.id === '') return;
    const savedId = typeof window !== 'undefined' ? sessionStorage.getItem('noor.activeTenderId') : null;
    if (savedId) {
      const saved = tenants.find((t) => String(t.id) === savedId);
      if (saved) {
        onTenantChange(tenantFromTender(saved));
        return;
      }
    }
    if (tenants.length > 0 && !tenants.some((t) => String(t.id) === tenant.id)) {
      onTenantChange(tenantFromTender(tenants[0]));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadingList, tenants]);

  // حفظ المنافسة النشطة عند تغييرها
  useEffect(() => {
    if (typeof window !== 'undefined' && tenant.id && tenant.id !== '1') {
      sessionStorage.setItem('noor.activeTenderId', tenant.id);
    }
  }, [tenant.id]);

  /** حفظ إعادة تسمية منافسة من القائمة */
  const handleRenameSave = async (id: number) => {
    if (!renameTitle.trim() || renaming) return;
    setRenaming(true);
    try {
      const updated = await renameTender(id, renameTitle.trim(), renameClient.trim());
      await load();
      // مزامنة الهوية النشطة إن كانت هي المعنية
      if (String(id) === tenant.id) onTenantChange(tenantFromTender(updated));
      setRenamingId(null);
    } catch {
      /* الخطأ يظهر ببقاء وضع التحرير */
    } finally {
      setRenaming(false);
    }
  };

  /** «بدء من جديد» — يمسح الجلسة الحالية فقط (لا يحذف أي بيانات) ويبدأ من أول منافسة */
  const handleResetSession = async () => {
    sessionStorage.removeItem('noor.activeTenderId');
    // نبدأ من أول منافسة في القائمة دائماً
    const list = await load();
    if (list.length > 0) {
      const first = tenantFromTender(list[0]);
      // إن كنا على نفس المنافسة، onTenantChange بنفس القيمة لن يعيد الرندر —
      // لذا نطلق حدث session-reset الذي يصفّر حالات الشاشة كلها (epoch)
      onTenantChange(first);
    }
    window.dispatchEvent(new CustomEvent('noor.session-reset'));
    setMenuOpen(false);
  };

  // إغلاق القائمة عند النقر خارجها
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    if (menuOpen) document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [menuOpen]);

  // مزامنة فورية بعد رفع حزمة جديدة (يرسلها UploadTenderModal)
  useEffect(() => {
    const onTendersChanged = (e: Event) => {
      load().then((list) => {
        const detail = (e as CustomEvent).detail as { tenderId?: number } | undefined;
        if (detail?.tenderId) {
          const created = list.find((t) => t.id === detail.tenderId);
          if (created) onTenantChange(tenantFromTender(created));
        }
      });
    };
    window.addEventListener('tenders-changed', onTendersChanged);
    return () => window.removeEventListener('tenders-changed', onTendersChanged);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  const handleCreate = async () => {
    if (!newTitle.trim() || creating) return;
    setCreating(true);
    try {
      const created = await createTender(newTitle.trim(), newClient.trim());
      await load();
      onTenantChange(tenantFromTender(created));
      setNewTitle('');
      setNewClient('');
      setCreating(false);
      setMenuOpen(false);
    } catch {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    setConfirmDeleteId(null);
    try {
      await deleteTender(id);
      const remaining = await load();
      if (String(id) === tenant.id) {
        if (remaining.length > 0) onTenantChange(tenantFromTender(remaining[0]));
        else window.location.reload(); // لا مزيد من المنافسات — إعادة تهيئة نظيفة
      }
    } catch { /* أظهر الخطأ عبر بقاء العنصر */ }
  };

  const activeTender = tenants.find((t) => String(t.id) === tenant.id);
  const isBlank = tenant.id === '';

  return (
    <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur border-b border-slate-700/60 shadow-lg">
      <div className="max-w-[1400px] mx-auto px-4 md:px-6">
        <div className="flex items-center justify-between h-16 gap-3">
          {/* Brand */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-teal-400 to-blue-600 flex items-center justify-center shrink-0 shadow-lg shadow-teal-500/20">
              <Boxes className="h-6 w-6 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-sm md:text-base font-black text-white tracking-tight truncate leading-tight">
                منظومة النور
              </h1>
              <p className="hidden sm:flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-teal-400 font-bold">
                <Radio size={10} className="animate-pulse" /> {t("tagline", lang)}
              </p>
            </div>
          </div>

          {/* Dynamic workspace switcher + actions (desktop) */}
          <div className="hidden lg:flex items-center gap-3">
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="flex items-center gap-2 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-600/60 rounded-lg px-3 py-2 text-left transition"
              >
                <Building2 className="h-4 w-4 text-teal-400 shrink-0" />
                <span className="text-xs font-semibold text-white truncate max-w-[220px]">
                  {activeTender ? activeTender.title : loadingList ? 'Loading workspaces…' : 'No tender selected'}
                </span>
                {activeTender && (
                  <span className={`text-[9px] font-black uppercase tracking-wider border rounded-full px-2 py-0.5 ${PHASE_STYLE[tenant.phase] || PHASE_STYLE.Draft}`}>
                    {tenant.phase}
                  </span>
                )}
                <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-96 rounded-xl border border-slate-700 bg-slate-800 shadow-2xl overflow-hidden z-50 max-h-[70vh] flex flex-col">
                  <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-700 bg-slate-900/60">
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Workspaces — live from database</span>
                    <button onClick={() => load()} className="p-1 rounded text-slate-400 hover:text-white" aria-label="Refresh list">
                      <RefreshCw className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <div className="overflow-y-auto flex-1">
                    {loadingList && (
                      <div className="flex items-center justify-center py-8 text-slate-400">
                        <Loader2 className="h-5 w-5 animate-spin" />
                      </div>
                    )}
                    {!loadingList && tenants.length === 0 && (
                      <p className="text-xs text-slate-400 text-center py-6 px-4">
                        لا توجد منافسات بعد — أنشئ مساحة عمل جديدة أو ارفع حزمة منافسة.
                      </p>
                    )}
                    {tenants.map((t) => {
                      const active = String(t.id) === tenant.id;
                      const phase = t.status === 'completed' ? 'Completed' : t.status === 'processing' ? 'Swarm Running' : 'Draft';
                      return (
                        <div
                          key={t.id}
                          className={`group w-full flex items-start gap-3 px-4 py-3 text-left border-l-2 transition ${
                            active ? 'bg-slate-700/40 border-teal-400' : 'border-transparent hover:bg-slate-700/30'
                          }`}
                        >
                          <button
                            className="flex items-start gap-3 min-w-0 flex-1"
                            onClick={() => { onTenantChange(tenantFromTender(t)); setMenuOpen(false); }}
                          >
                            <Building2 className="h-4 w-4 text-teal-400 mt-0.5 shrink-0" />
                            <div className="min-w-0">
                              <p className="text-sm font-bold text-white truncate">{t.title}</p>
                              <p className="text-xs text-slate-400 truncate">{t.client_name}</p>
                              <p className="text-[10px] mt-0.5">
                                <span className={`uppercase tracking-wider font-bold border rounded-full px-2 py-0.5 ${PHASE_STYLE[phase] || PHASE_STYLE.Draft}`}>{phase}</span>
                                <span className="text-slate-500 ml-2">{t.document_count} docs</span>
                                {t.technical_score !== null && (
                                  <span className="text-emerald-400 ml-2 font-mono">{t.technical_score}/100</span>
                                )}
                              </p>
                            </div>
                          </button>
                          {confirmDeleteId === t.id ? (
                            <div className="flex items-center gap-1 shrink-0">
                              <button
                                onClick={() => handleDelete(t.id)}
                                title="تأكيد الحذف النهائي (المستندات والنتائج وكل ما يتعلق بها)"
                                className="p-1.5 rounded-md bg-rose-600/90 text-white hover:bg-rose-500"
                              >
                                <Check className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => setConfirmDeleteId(null)}
                                className="p-1.5 rounded-md text-slate-300 hover:bg-slate-600"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={(e) => { e.stopPropagation(); setConfirmDeleteId(t.id); }}
                              title="حذف هذه المنافسة نهائياً"
                              className="p-1.5 rounded-md text-slate-500 opacity-0 group-hover:opacity-100 hover:text-rose-400 hover:bg-slate-800 transition"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Create-new inline form */}
                  <div className="border-t border-slate-700 p-3 space-y-2 bg-slate-900/40">
                    <input
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                      placeholder="اسم المنافسة الجديدة…"
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500/60"
                    />
                    <div className="flex gap-2">
                      <input
                        value={newClient}
                        onChange={(e) => setNewClient(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                        placeholder="الجهة المالكة (اختياري)"
                        className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-teal-500/60"
                      />
                      <button
                        onClick={handleCreate}
                        disabled={!newTitle.trim() || creating}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black uppercase tracking-wider bg-gradient-to-r from-teal-500 to-blue-600 text-white disabled:opacity-40"
                      >
                        {creating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Plus className="h-3.5 w-3.5" />}
                        New
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center gap-2 bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-semibold text-white">{tenant.role}</span>
            </div>

            {/* بدء من جديد — جلسة نظيفة دون حذف البيانات */}
            <button
              onClick={handleResetSession}
              title={t("startFreshHint", lang)}
              className="flex items-center gap-1.5 text-xs font-bold text-slate-300 border border-slate-600 hover:border-teal-500/50 hover:text-teal-300 px-3 py-2.5 rounded-lg transition"
            >
              <RotateCcw className="h-4 w-4" />
              {t("startFresh", lang)}
            </button>

            <button
              onClick={() => (tenant.id === '' ? onNewCompetition() : onUploadClick())}
              title={tenant.id === ''
                ? 'ابدأ منافسة جديدة: الاسم ثم الكراسة ثم قرار الإطلاق'
                : 'أضف ملفات إلى المنافسة النشطة'}
              className="flex items-center gap-2 bg-gradient-to-r from-teal-500 to-blue-600 hover:from-teal-400 hover:to-blue-500 text-white font-bold text-sm px-4 py-2.5 rounded-lg shadow-lg shadow-blue-500/20 transition"
            >
              <UploadCloud className="h-4 w-4" />
              {tenant.id === '' ? 'منافسة جديدة' : t("uploadTenderPackage", lang)}
            </button>

            {/* مولد العروض الهندسية (ATPAS) */}
            <button
              onClick={() => router.push('/proposal-builder')}
              title="مولد العروض الهندسية — ATPAS"
              className="flex items-center gap-1.5 text-xs font-bold text-slate-300 border border-slate-600 hover:border-teal-500/50 hover:text-teal-300 px-3 py-2.5 rounded-lg transition"
            >
              <FileText className="h-4 w-4" />
              مولد العروض
            </button>

            {/* تبديل اللغة عربي/إنجليزي */}
            <button
              onClick={toggleLang}
              title="Switch language / تغيير اللغة"
              className="flex items-center gap-1.5 text-xs font-bold text-slate-300 border border-slate-600 hover:border-cyan-500/50 hover:text-cyan-300 px-3 py-2.5 rounded-lg transition"
            >
              <Languages className="h-4 w-4" />
              {lang === 'ar' ? 'EN' : 'ع'}
            </button>

            <button
              onClick={() => router.push('/settings')}
              title={t("settings", lang)}
              className="p-2.5 rounded-lg border border-slate-600/60 text-slate-300 hover:text-teal-400 hover:border-teal-500/40 hover:bg-slate-800 transition"
              aria-label={t("settings", lang)}
            >
              <Settings className="h-4.5 w-4.5" />
            </button>
          </div>

          {/* Mobile actions */}
          <div className="flex lg:hidden items-center gap-2">
            <button onClick={() => router.push('/proposal-builder')}
              className="p-2 rounded-lg text-slate-300 hover:text-teal-400 hover:bg-slate-800 transition" aria-label="مولد العروض">
              <FileText className="h-5 w-5" />
            </button>
            <button onClick={() => router.push('/settings')}
              className="p-2 rounded-lg text-slate-300 hover:text-teal-400 hover:bg-slate-800 transition" aria-label="Settings">
              <Settings className="h-5 w-5" />
            </button>
            <button
              onClick={() => (tenant.id === '' ? onNewCompetition() : onUploadClick())}
              className="flex items-center gap-1.5 bg-gradient-to-r from-teal-500 to-blue-600 text-white font-bold text-xs px-3 py-2.5 rounded-lg transition"
            >
              <UploadCloud className="h-4 w-4" />
              Upload
            </button>
            <button
              onClick={() => setMobileMenuOpen((v) => !v)}
              className="p-2.5 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile dynamic drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-700/60 bg-slate-900 px-4 py-3 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold">Active Workspace</p>
            <button onClick={() => load()} className="text-slate-400"><RefreshCw className="h-3.5 w-3.5" /></button>
          </div>
          <select
            value={tenant.id}
            onChange={(e) => {
              const t = tenants.find((x) => String(x.id) === e.target.value);
              if (t) onTenantChange(tenantFromTender(t));
            }}
            className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white"
          >
            {tenants.map((t) => (
              <option key={t.id} value={String(t.id)}>
                {t.title} — {t.client_name}
              </option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-2">
            <input value={newTitle} onChange={(e) => setNewTitle(e.target.value)} placeholder="منافسة جديدة…"
              className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-xs text-white placeholder:text-slate-500" />
            <button onClick={handleCreate} disabled={!newTitle.trim() || creating}
              className="flex items-center justify-center gap-1 rounded-lg text-xs font-black bg-gradient-to-r from-teal-500 to-blue-600 text-white disabled:opacity-40">
              <Plus className="h-3.5 w-3.5" /> Create
            </button>
          </div>
          {activeTender && (
            <button
              onClick={() => setConfirmDeleteId(activeTender.id)}
              className="w-full flex items-center justify-center gap-1.5 text-[11px] font-black uppercase tracking-wider border border-rose-500/40 text-rose-300 rounded-lg px-3 py-2 hover:bg-rose-500/10"
            >
              <Trash2 className="h-3.5 w-3.5" /> حذف المنافسة الحالية
            </button>
          )}
          {confirmDeleteId !== null && (
            <div className="rounded-lg border border-rose-500/50 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
              سيُحذف كل شيء نهائياً (المستندات والنتائج). متأكد؟
              <div className="flex gap-2 mt-2">
                <button onClick={() => handleDelete(confirmDeleteId)} className="flex-1 bg-rose-600 rounded-md py-1.5 font-bold text-white">نعم، احذف</button>
                <button onClick={() => setConfirmDeleteId(null)} className="flex-1 border border-slate-500 rounded-md py-1.5 text-slate-200">إلغاء</button>
              </div>
            </div>
          )}
          <div className="flex items-center gap-2 bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
            <span className="text-xs text-white truncate">{tenant.role}</span>
          </div>
        </div>
      )}
    </header>
  );
};
