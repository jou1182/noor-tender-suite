"use client";

/**
 * NewCompetitionWizard — معالج إنشاء منافسة جديدة (الحلقة المفقودة).
 *
 * رحلة قائد فريق العروض:
 *  1) بيانات المنافسة: الاسم + العميل (مثال: صيانة طريق مكة-جدة / هيئة الطرق)
 *  2) ملفات الكراسة (RFP + جدول XER اختياري) — متعددة
 *  3) اختيار: إطلاق السرب فوراً أم لاحقاً (الافتراضي: لاحقاً — أضف عرض الفريق أولاً)
 *
 * النتيجة: منافسة مسماة صحيحاً + ملفاتها + عرض الفريق يُرفع بعدها من زره المخصص.
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  X, Loader2, FileText, FileCode, UploadCloud, Rocket, Clock,
  Building2, FolderOpen, CheckCircle2, ArrowRight,
} from 'lucide-react';
import { createTender, uploadTenderFiles, launchTenderSwarm, type TenderSummary } from '../lib/tenders_client';

const API = 'http://localhost:8000';

interface Props {
  open: boolean;
  onClose: () => void;
  /** تُستدعى بعد الإنشاء الناجح بالمنافسة الجديدة */
  onCreated: (t: TenderSummary) => void;
}

type Step = 1 | 2 | 3;

export const NewCompetitionWizard: React.FC<Props> = ({ open, onClose, onCreated }) => {
  const [step, setStep] = useState<Step>(1);
  const [title, setTitle] = useState('');
  const [client, setClient] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [launchNow, setLaunchNow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState<TenderSummary | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setStep(1); setTitle(''); setClient(''); setFiles([]);
      setLaunchNow(false); setError(''); setCreated(null);
    }
  }, [open]);

  if (!open) return null;

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name + f.size));
      return [...prev, ...Array.from(list).filter((f) => !names.has(f.name + f.size))];
    });
  };

  const canNext1 = title.trim().length >= 3;
  const canNext2 = files.length > 0;
  const hasXer = files.some((f) => f.name.toLowerCase().endsWith('.xer'));

  const finish = async () => {
    setBusy(true);
    setError('');
    try {
      // 1) إنشاء المنافسة باسمها الصحيح
      const tender = await createTender(title.trim(), client.trim() || '—');
      // 2) رفع الملفات إليها
      await uploadTenderFiles(tender.id, files, hasXer);
      // 3) إطلاق السرب؟ (اختياري — الافتراضي لا: أضف عرض الفريق أولاً)
      if (launchNow && hasXer) {
        await launchTenderSwarm(tender.id);
      }
      setCreated(tender);
      onCreated(tender);
      setTimeout(onClose, 900);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'فشل إنشاء المنافسة');
    } finally {
      setBusy(false);
    }
  };

  const fileIcon = (name: string) =>
    name.toLowerCase().endsWith('.xer')
      ? <FileCode className="h-4 w-4 text-blue-400" />
      : <FileText className="h-4 w-4 text-rose-400" />;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={() => !busy && onClose()} />
      <div className="relative w-full max-w-xl bg-slate-900 rounded-2xl shadow-2xl border border-slate-700 overflow-hidden" dir="rtl">

        {/* الترويسة + مؤشر الخطوات */}
        <div className="px-6 py-4 border-b border-slate-700 bg-slate-950/60">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-black text-white flex items-center gap-2">
              <FolderOpen className="h-5 w-5 text-teal-400" />
              منافسة جديدة
            </h2>
            <button onClick={() => !busy && onClose()} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="flex items-center gap-2 mt-3">
            {([['1', 'بيانات المنافسة'], ['2', 'ملفات الكراسة'], ['3', 'الإطلاق']] as const).map(([n, label], i) => (
              <React.Fragment key={n}>
                <div className={`flex items-center gap-1.5 text-[11px] font-black ${step >= Number(n) ? 'text-teal-300' : 'text-slate-500'}`}>
                  <span className={`h-5 w-5 rounded-full flex items-center justify-center border text-[10px] ${
                    step > Number(n) ? 'bg-teal-500 border-teal-500 text-white' : step === Number(n) ? 'border-teal-400 text-teal-300' : 'border-slate-600'
                  }`}>
                    {step > Number(n) ? <CheckCircle2 className="h-3.5 w-3.5" /> : n}
                  </span>
                  {label}
                </div>
                {i < 2 && <div className={`flex-1 h-px ${step > Number(n) ? 'bg-teal-500/60' : 'bg-slate-700'}`} />}
              </React.Fragment>
            ))}
          </div>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <p className="text-xs text-rose-300 font-semibold bg-rose-500/10 border border-rose-500/30 rounded-lg px-3 py-2" dir="rtl">⚠ {error}</p>
          )}

          {/* الخطوة 1: البيانات */}
          {step === 1 && (
            <div className="space-y-4">
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-1.5">
                  <FileText className="h-3 w-3" /> اسم المنافسة
                </span>
                <input value={title} onChange={(e) => setTitle(e.target.value)}
                  placeholder="مثال: صيانة طريق مكة - جدة"
                  autoFocus
                  className="mt-1.5 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-teal-500" />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-1.5">
                  <Building2 className="h-3 w-3" /> جهة العميل (اختياري)
                </span>
                <input value={client} onChange={(e) => setClient(e.target.value)}
                  placeholder="مثال: هيئة الطرق والسلامة المرورية"
                  className="mt-1.5 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-teal-500" />
              </label>
            </div>
          )}

          {/* الخطوة 2: الملفات */}
          {step === 2 && (
            <div className="space-y-3">
              <button onClick={() => inputRef.current?.click()}
                className="w-full border-2 border-dashed border-slate-600 hover:border-teal-500/60 rounded-xl p-6 text-center transition group">
                <UploadCloud className="h-8 w-8 text-slate-500 group-hover:text-teal-400 mx-auto mb-2" />
                <p className="text-sm font-bold text-slate-300">أضف ملفات كراسة المنافسة</p>
                <p className="text-xs text-slate-500 mt-1">PDF للكراسة والملاحق + ملف XER للجدول الزمني إن وُجد</p>
              </button>
              <input ref={inputRef} type="file" multiple hidden
                accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv,.xer"
                onChange={(e) => { addFiles(e.target.files); if (inputRef.current) inputRef.current.value = ''; }} />

              {files.length > 0 && (
                <div className="rounded-lg border border-slate-700 bg-slate-950/50 divide-y divide-slate-800 max-h-48 overflow-y-auto">
                  {files.map((f) => (
                    <div key={f.name + f.size} className="flex items-center gap-2 px-3 py-2">
                      {fileIcon(f.name)}
                      <span className="text-xs text-slate-300 truncate flex-1" dir="auto">{f.name}</span>
                      <span className="text-[10px] font-mono text-slate-500">{(f.size / (1024 * 1024)).toFixed(1)}MB</span>
                      <button onClick={() => setFiles((prev) => prev.filter((x) => x !== f))}
                        className="p-1 text-slate-500 hover:text-rose-400"><X className="h-3 w-3" /></button>
                    </div>
                  ))}
                </div>
              )}

              {!hasXer && files.length > 0 && (
                <p className="text-[11px] text-amber-300/90" dir="rtl">
                  ℹ️ لا يوجد ملف XER — سيعمل السرب بلا تحليل الجدول الزمني (يمكنك إضافته لاحقاً).
                </p>
              )}
            </div>
          )}

          {/* الخطوة 3: الإطلاق */}
          {step === 3 && (
            <div className="space-y-4">
              <div className="rounded-xl border border-slate-700 bg-slate-950/50 p-4 space-y-1.5" dir="rtl">
                <p className="text-sm font-bold text-white">{title}</p>
                {client && <p className="text-xs text-slate-400">{client}</p>}
                <p className="text-xs text-teal-300">{files.length} ملف جاهز</p>
              </div>

              <div className="space-y-2">
                <button onClick={() => setLaunchNow(false)}
                  className={`w-full text-right p-4 rounded-xl border transition ${!launchNow ? 'border-teal-500 bg-teal-500/10' : 'border-slate-700 hover:border-slate-500'}`}>
                  <span className="flex items-center gap-2 text-sm font-bold text-white">
                    <Clock className="h-4 w-4 text-teal-400" /> لاحقاً — أضيف عرض الفريق أولاً (موصى به)
                  </span>
                  <span className="block text-xs text-slate-400 mt-1 leading-relaxed">
                    تُنشأ المنافسة وملفاتها، ثم ترفع العرض الفني من زره المخصص، وتطلق السرب لتقييم شامل في النهاية.
                  </span>
                </button>
                <button onClick={() => { setLaunchNow(true); }} disabled={!hasXer}
                  title={!hasXer ? 'الإطلاق يتطلب ملف XER للجدول الزمني' : ''}
                  className={`w-full text-right p-4 rounded-xl border transition disabled:opacity-40 ${launchNow ? 'border-fuchsia-500 bg-fuchsia-500/10' : 'border-slate-700 hover:border-slate-500'}`}>
                  <span className="flex items-center gap-2 text-sm font-bold text-white">
                    <Rocket className="h-4 w-4 text-fuchsia-400" /> الآن — أطلق السرب فوراً على الكراسة
                  </span>
                  <span className="block text-xs text-slate-400 mt-1 leading-relaxed">
                    تحليل فوري للكراسة (امتثال، مواصفات، جدول) — مناسب للاستكشاف السريع.
                  </span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* التذييل: أزرار التنقل */}
        <div className="px-6 py-4 border-t border-slate-700 bg-slate-950/60 flex items-center justify-between">
          <button onClick={() => (step === 1 ? onClose() : setStep((step - 1) as Step))}
            disabled={busy}
            className="px-4 py-2 rounded-lg text-sm font-bold text-slate-300 hover:bg-slate-800 disabled:opacity-40">
            {step === 1 ? 'إلغاء' : 'السابق'}
          </button>

          {step === 1 && (
            <button onClick={() => setStep(2)} disabled={!canNext1}
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg text-sm font-black bg-gradient-to-r from-teal-500 to-blue-600 text-white disabled:opacity-40">
              التالي: الملفات <ArrowRight className="h-4 w-4" />
            </button>
          )}
          {step === 2 && (
            <button onClick={() => setStep(3)} disabled={!canNext2}
              className="flex items-center gap-1.5 px-5 py-2 rounded-lg text-sm font-black bg-gradient-to-r from-teal-500 to-blue-600 text-white disabled:opacity-40">
              التالي: الإطلاق <ArrowRight className="h-4 w-4" />
            </button>
          )}
          {step === 3 && (
            <button onClick={finish} disabled={busy}
              className="flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-black bg-gradient-to-r from-teal-500 to-blue-600 text-white disabled:opacity-50">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              {busy ? 'جارٍ الإنشاء…' : launchNow ? 'إنشاء + إطلاق السرب' : 'إنشاء المنافسة'}
            </button>
          )}
        </div>

        {/* نجاح */}
        {created && (
          <div className="absolute inset-0 bg-slate-950/90 flex items-center justify-center" dir="rtl">
            <div className="text-center space-y-2">
              <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto" />
              <p className="text-lg font-black text-white">تم إنشاء المنافسة</p>
              <p className="text-sm text-teal-300">{created.title}</p>
              {!launchNow && (
                <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                  الخطوة التالية: ارفع العرض الفني من الزر البنفسجي «رفع العرض الفني» ثم أطلق السرب.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
