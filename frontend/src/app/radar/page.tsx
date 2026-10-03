"use client";

/**
 * رادار المنافسات — صفحة عربية تعرض حالة خدمة المزامنة المحلية (Etimad)
 * عبر جسر /api/v1/radar. عند توقف الخدمة تظهر لوحة تشغيل واضحة بدل الأعطال.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowRight, Building2, CalendarClock, CheckCircle2, ExternalLink,
  FileSearch, Loader2, MapPin, Radar, RefreshCw, Trophy, XCircle,
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

interface HealthInfo {
  online: boolean;
  serviceVersion?: string;
  browser?: { mode?: string; connected?: boolean; endpoint?: string };
  database?: { online?: boolean; schemaVersion?: number };
  message?: string;
}

interface Snapshot {
  online: boolean;
  lastSyncAt?: string | null;
  checked?: number;
  regions?: number;
  newItems?: number;
  changedItems?: number;
  items?: TenderItem[];
  details?: { inspected?: number; complete?: number; failed?: number };
  message?: string;
}

interface TenderItem {
  reference: string;
  title: string;
  agency?: string;
  region?: string;
  deadline?: string | null;
  status?: string;
  score?: number;
  etimadUrl?: string;
  tenderNumber?: string;
}

export default function RadarPage() {
  const router = useRouter();
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true); else setRefreshing(true);
    try {
      const [h, t] = await Promise.all([
        fetch(`${API}/api/v1/radar/health`).then((r) => r.json()),
        fetch(`${API}/api/v1/radar/tenders`).then((r) => r.json()),
      ]);
      setHealth(h); setSnap(t);
    } catch {
      setHealth({ online: false, message: 'تعذر الاتصال بخادم المنظومة' });
      setSnap({ online: false, items: [] });
    } finally {
      setLoading(false); setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const items = snap?.items ?? [];
  const stats = [
    { label: 'مناطق مغطاة', value: snap?.regions ?? 0, icon: MapPin },
    { label: 'منافسة جديدة', value: snap?.newItems ?? 0, icon: Trophy },
    { label: 'تغيّرت', value: snap?.changedItems ?? 0, icon: RefreshCw },
    { label: 'تفاصيل مفحوصة', value: snap?.details?.complete ?? 0, icon: FileSearch },
  ];

  return (
    <main dir="rtl" className="min-h-screen bg-slate-950 text-white" style={{ fontFamily: 'var(--font-tajawal), Tajawal, sans-serif' }}>
      {/* الشريط العلوي */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/')} className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition" aria-label="رجوع">
              <ArrowRight className="h-5 w-5" />
            </button>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Radar className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-base font-black tracking-tight">رادار المنافسات</h1>
              <p className="text-[10px] uppercase tracking-widest text-cyan-400 font-bold">رصد منصة اعتماد — Tender Radar</p>
            </div>
          </div>
          <button
            onClick={() => load(true)}
            disabled={refreshing}
            className="flex items-center gap-1.5 text-xs font-bold text-slate-300 border border-slate-600 hover:border-cyan-500/50 hover:text-cyan-300 px-3 py-2 rounded-lg transition disabled:opacity-40"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            تحديث
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
        {loading && (
          <div className="flex items-center justify-center py-16 text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        )}

        {!loading && health && !health.online && (
          <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 px-6 py-8 text-center space-y-4">
            <XCircle className="h-10 w-10 text-amber-400 mx-auto" />
            <div>
              <h2 className="font-black text-lg">خدمة الرادار متوقفة</h2>
              <p className="text-sm text-slate-300 mt-1">{health.message ?? 'لم يتم تشغيل خدمة المزامنة بعد'}</p>
            </div>
            <div className="text-right bg-slate-900/70 border border-slate-700 rounded-xl p-4 font-mono text-xs text-slate-300" dir="ltr">
              npm --prefix radar run start
            </div>
            <p className="text-[11px] text-slate-400">أو شغّل «Noor.bat» — يبدأ الخدمة تلقائياً مع المنصة (يتطلب Node.js ≥ 22.13)</p>
          </div>
        )}

        {!loading && health?.online && (
          <>
            {/* حالة الخدمة */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">الخدمة</p>
                  <p className="text-sm font-bold">متصلة — مخطط v{health.database?.schemaVersion ?? '؟'}</p>
                </div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 flex items-center gap-3">
                {health.browser?.connected
                  ? <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                  : <XCircle className="h-5 w-5 text-slate-500 shrink-0" />}
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">جلسة Chrome البشرية</p>
                  <p className="text-sm font-bold">{health.browser?.connected ? 'متصلة' : 'غير متصلة — سجّل الدخول من نافذة الرادار'}</p>
                </div>
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-3 flex items-center gap-3">
                <CalendarClock className="h-5 w-5 text-cyan-400 shrink-0" />
                <div>
                  <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">آخر مزامنة كاملة</p>
                  <p className="text-sm font-bold">{snap?.lastSyncAt ? new Date(snap.lastSyncAt).toLocaleString('ar-SA') : 'لم تتم بعد'}</p>
                </div>
              </div>
            </div>

            {/* إحصاءات الجولة */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {stats.map((s) => (
                <div key={s.label} className="rounded-xl border border-slate-800 bg-slate-900/60 px-4 py-4 text-center">
                  <s.icon className="h-5 w-5 text-cyan-400 mx-auto mb-2" />
                  <p className="text-2xl font-black">{s.value}</p>
                  <p className="text-[11px] text-slate-400 font-bold">{s.label}</p>
                </div>
              ))}
            </div>

            {/* المنافسات الرصدت */}
            <section>
              <h2 className="text-sm font-black text-slate-300 mb-3">
                المنافسات المرصودة
                <span className="text-cyan-400 text-xs font-bold">({items.length})</span>
              </h2>
              {items.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-700 px-4 py-12 text-center text-sm text-slate-500">
                  لا توجد منافسات محفوظة بعد — شغّل أول جولة مزامنة من خدمة الرادار.
                </div>
              ) : (
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-right text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900 text-[10px] uppercase tracking-wider text-slate-500">
                          <th className="px-4 py-2.5 font-bold">المرجع</th>
                          <th className="px-4 py-2.5 font-bold">المنافسة</th>
                          <th className="px-4 py-2.5 font-bold">الجهة</th>
                          <th className="px-4 py-2.5 font-bold">المنطقة</th>
                          <th className="px-4 py-2.5 font-bold">الحالة</th>
                          <th className="px-4 py-2.5 font-bold">الاستحقاق</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {items.map((t) => (
                          <tr key={t.reference} className="hover:bg-slate-800/30 transition">
                            <td className="px-4 py-3 font-mono text-[11px] text-slate-400" dir="ltr">{t.reference}</td>
                            <td className="px-4 py-3">
                              <p className="font-semibold text-white leading-tight">{t.title}</p>
                              {t.etimadUrl && (
                                <a href={t.etimadUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-[10px] text-cyan-400 hover:text-cyan-300 mt-0.5">
                                  اعتماد <ExternalLink className="h-3 w-3" />
                                </a>
                              )}
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-300">
                              <span className="inline-flex items-center gap-1"><Building2 className="h-3.5 w-3.5 text-slate-500" />{t.agency ?? '—'}</span>
                            </td>
                            <td className="px-4 py-3 text-xs text-slate-300">{t.region ?? '—'}</td>
                            <td className="px-4 py-3"><span className="text-[10px] font-bold border border-slate-600 rounded-full px-2 py-0.5 text-slate-300">{t.status ?? 'جديدة'}</span></td>
                            <td className="px-4 py-3 text-xs text-slate-300">{t.deadline ? new Date(t.deadline).toLocaleDateString('ar-SA') : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
