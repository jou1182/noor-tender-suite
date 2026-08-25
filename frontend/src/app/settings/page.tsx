"use client";

import React, { useCallback, useEffect, useState } from 'react';
import {
  ArrowLeft, PlugZap, RefreshCw, Bot, Loader2, ShieldCheck, Plus, Trash2,
  Play, X, Sparkles, Lock,
} from 'lucide-react';
import type {
  AgentEntry, ConnectionTestResult, LLMProvider, ProviderType,
} from '../../types/platform';
import { PROVIDER_META, ADD_FORM_DEFAULT } from '../../lib/provider_meta';

const API = 'http://localhost:8000';

type Tab = 'providers' | 'agents';

/** مسودة تعديل هوية الوكيل — تُحفظ فقط عند الضغط على حفظ. */
interface AgentDraft {
  name_ar: string;
  name_en: string;
  avatar_emoji: string;
  role: string;
  system_prompt: string;
  provider_id: number | null;
  model_override: string;
  temperature: number;
}

const draftFrom = (a: AgentEntry): AgentDraft => ({
  name_ar: a.name_ar, name_en: a.name_en, avatar_emoji: a.avatar_emoji, role: a.role,
  system_prompt: a.system_prompt, provider_id: a.provider_id,
  model_override: a.model_override, temperature: a.temperature,
});

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>('agents');
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [agents, setAgents] = useState<AgentEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, ConnectionTestResult>>({});
  const [savingAgent, setSavingAgent] = useState<string | null>(null);
  const [savedFlash, setSavedFlash] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState(ADD_FORM_DEFAULT);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [pRes, aRes] = await Promise.all([
        fetch(`${API}/api/v1/llm-providers`),
        fetch(`${API}/api/v1/agents`),
      ]);
      setProviders((await pRes.json()).providers || []);
      setAgents((await aRes.json()).agents || []);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const testProvider = async (id: number) => {
    setTesting(id);
    try {
      const res = await fetch(`${API}/api/v1/llm-providers/${id}/test`, { method: 'POST' });
      const result: ConnectionTestResult = await res.json();
      setTestResults((prev) => ({ ...prev, [id]: result }));
    } finally {
      setTesting(null);
    }
  };

  const toggleProvider = async (provider: LLMProvider) => {
    await fetch(`${API}/api/v1/llm-providers/${provider.id}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !provider.enabled }),
    });
    load();
  };

  const deleteProvider = async (id: number) => {
    await fetch(`${API}/api/v1/llm-providers/${id}`, { method: 'DELETE' });
    load();
  };

  const addProvider = async () => {
    if (!addForm.name) return;
    await fetch(`${API}/api/v1/llm-providers`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...addForm, enabled: true }),
    });
    setShowAdd(false);
    setAddForm(ADD_FORM_DEFAULT);
    load();
  };

  const saveAgent = async (agent: AgentEntry, patch: Partial<AgentEntry>) => {
    setSavingAgent(agent.key);
    try {
      await fetch(`${API}/api/v1/agents/${agent.key}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      setAgents((prev) => prev.map((a) => (a.key === agent.key ? { ...a, ...patch } : a)));
      setSavedFlash(agent.key);
      setTimeout(() => setSavedFlash(null), 1600);
    } finally {
      setSavingAgent(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Top bar */}
      <div className="bg-slate-900 border-b border-slate-700/60 sticky top-0 z-40">
        <div className="max-w-[1200px] mx-auto px-4 md:px-6 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button onClick={() => window.location.href = '/'} className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition" aria-label="Back to dashboard">
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-base font-black text-white tracking-tight">Platform Settings</h1>
              <p className="text-[10px] uppercase tracking-widest text-teal-400 font-bold">Dynamic Agents · LLM Gateway · Agent Training</p>
            </div>
          </div>
          <button onClick={load} className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition" aria-label="Refresh">
            <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="max-w-[1200px] mx-auto px-4 md:px-6 pt-6">
        <div className="inline-flex rounded-xl bg-slate-900 p-1 gap-1 border border-slate-700">
          {([['agents', 'Agent Registry & Training', Bot], ['providers', 'LLM Providers', PlugZap]] as const).map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => setTab(key as Tab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-black uppercase tracking-wider transition ${
                tab === key ? 'bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-[1200px] mx-auto px-4 md:px-6 py-6">
        {loading ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => <div key={i} className="h-28 rounded-xl bg-slate-800/60 animate-pulse" />)}
          </div>
        ) : tab === 'providers' ? (
          <ProvidersPanel
            providers={providers} testResults={testResults} testing={testing}
            onTest={testProvider} onToggle={toggleProvider} onDelete={deleteProvider}
            onShowAdd={() => setShowAdd(true)}
          />
        ) : (
          <AgentsPanel
            agents={agents} providers={providers}
            savingAgent={savingAgent} savedFlash={savedFlash}
            onSave={saveAgent}
          />
        )}
      </main>

      {showAdd && (
        <AddProviderModal
          form={addForm} setForm={setAddForm}
          onClose={() => setShowAdd(false)} onSubmit={addProvider}
        />
      )}
    </div>
  );
}

/* ============================== Providers ============================== */

function ProvidersPanel(props: {
  providers: LLMProvider[];
  testResults: Record<number, ConnectionTestResult>;
  testing: number | null;
  onTest: (id: number) => void;
  onToggle: (p: LLMProvider) => void;
  onDelete: (id: number) => void;
  onShowAdd: () => void;
}) {
  const { providers, testResults, testing, onTest, onToggle, onDelete, onShowAdd } = props;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-xs text-slate-400">
          وجّه ذكاء الوكلاء عبر مزودين سحابيين أو اشتغل محلياً وخاصاً تماماً عبر Ollama / LM Studio.
        </p>
        <button onClick={onShowAdd}
          className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-4 py-2 rounded-lg bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow disabled:opacity-50">
          <Plus className="h-4 w-4" /> Add Provider
        </button>
      </div>
      {providers.length === 0 && (
        <div className="bg-slate-900 rounded-xl border border-dashed border-slate-700 p-12 text-center">
          <p className="text-sm font-semibold text-slate-400">لا يوجد مزودون بعد — أضف مزوداً لتبدأ.</p>
        </div>
      )}
      {providers.map((provider) => {
        const meta = PROVIDER_META[provider.provider_type];
        const result = testResults[provider.id];
        return (
          <div key={provider.id} className="bg-slate-900 rounded-xl border border-slate-700/70 shadow-sm p-5">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-sm font-black text-white">{provider.name}</h3>
                  {provider.privacy_safe && (
                    <span className="text-[9px] font-black uppercase tracking-wider bg-teal-500/15 text-teal-300 border border-teal-500/40 px-2 py-0.5 rounded-full">🔒 Private</span>
                  )}
                  {provider.is_default && (
                    <span className="text-[9px] font-black uppercase tracking-wider bg-blue-500/15 text-blue-300 border border-blue-500/40 px-2 py-0.5 rounded-full">Default</span>
                  )}
                </div>
                <p className="text-xs text-slate-400 font-mono mt-1 truncate">{provider.base_url} · {provider.model || 'no model'}</p>
                {provider.has_api_key && <p className="text-[10px] text-slate-500 font-mono">key: {provider.api_key_masked}</p>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => onToggle(provider)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${provider.enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
                  aria-label="Toggle enabled"
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${provider.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
                </button>
                <button onClick={() => onTest(provider.id)} disabled={testing === provider.id}
                  className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border border-slate-600 text-slate-200 hover:bg-slate-800 disabled:opacity-50">
                  {testing === provider.id ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <PlugZap className="h-3.5 w-3.5" />}
                  Test
                </button>
                <button onClick={() => onDelete(provider.id)}
                  className="flex items-center gap-1 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border border-rose-500/40 text-rose-300 hover:bg-rose-500/10">
                  <Trash2 className="h-3 w-3" /> Delete
                </button>
              </div>
            </div>
            {result && (
              <div className={`mt-3 rounded-lg border px-3 py-2 text-xs ${result.ok ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300' : 'border-rose-500/40 bg-rose-500/10 text-rose-300'}`}>
                {result.ok ? (
                  <span className="font-semibold">Connected in {result.latency_ms}ms — {result.models.length} models available{result.models.length ? `: ${result.models.slice(0, 5).join(', ')}` : ''}</span>
                ) : (
                  <span className="font-semibold">Failed: {result.error || 'unreachable'}</span>
                )}
              </div>
            )}
            <p className="mt-2 text-[10px] text-slate-500 uppercase tracking-wider font-bold">{meta?.label || provider.provider_type}</p>
          </div>
        );
      })}
    </div>
  );
}

/* ================================ Agents ================================ */

function AgentsPanel(props: {
  agents: AgentEntry[];
  providers: LLMProvider[];
  savingAgent: string | null;
  savedFlash: string | null;
  onSave: (agent: AgentEntry, patch: Partial<AgentEntry>) => void;
}) {
  const { agents, providers, savingAgent, savedFlash, onSave } = props;

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-400 leading-relaxed">
        كل شيء قابل للتعديل هنا: <span className="text-white font-bold">الاسم العربي والإنجليزي والصورة والدور وبرومبت التدريب</span> —
        عدّل ما تريد ثم اضغط <span className="text-teal-300 font-bold">حفظ</span>، أو جرّب سلوك الوكيل مباشرة بـ
        <span className="text-cyan-300 font-bold"> تجربة</span> قبل الحفظ. السرب يقرأ هذا السجل عند كل تشغيل.
      </p>
      {agents.map((agent) => (
        <AgentCard
          key={agent.key}
          agent={agent}
          providers={providers.filter((p) => p.enabled)}
          saving={savingAgent === agent.key}
          saved={savedFlash === agent.key}
          onSave={(patch) => onSave(agent, patch)}
        />
      ))}
    </div>
  );
}

function AgentCard(props: {
  agent: AgentEntry;
  providers: LLMProvider[];
  saving: boolean;
  saved: boolean;
  onSave: (patch: Partial<AgentEntry>) => void;
}) {
  const { agent, providers, saving, saved, onSave } = props;
  const [draft, setDraft] = useState<AgentDraft>(draftFrom(agent));
  const [showPrompt, setShowPrompt] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    setDraft(draftFrom(agent));
    setDirty(false);
  }, [agent]);

  const edit = (patch: Partial<AgentDraft>) => {
    setDraft((d) => ({ ...d, ...patch }));
    setDirty(true);
  };

  const handleSave = () => {
    onSave({ ...draft });
    setDirty(false);
  };

  const preview = useAgentPreview(agent, draft);

  const disabledStyle = !agent.enabled;

  return (
    <div className={`bg-slate-900 rounded-xl border shadow-sm p-5 transition ${disabledStyle ? 'border-slate-800 opacity-70' : dirty ? 'border-teal-500/50' : 'border-slate-700/70'}`}>
      {/* Identity row */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3 min-w-0">
          <input
            value={draft.avatar_emoji}
            onChange={(e) => edit({ avatar_emoji: e.target.value.slice(0, 2) })}
            title="صورة الوكيل (إيموجي — قابل للتعديل)"
            className="h-12 w-12 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600 flex items-center justify-center text-2xl text-center focus:outline-none focus:border-teal-500"
          />
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {/* الاسم الإنجليزي — الآن قابل للتعديل أيضاً */}
              <input
                value={draft.name_en}
                onChange={(e) => edit({ name_en: e.target.value })}
                placeholder="English name"
                className="bg-transparent border-b border-transparent hover:border-slate-600 focus:border-teal-500 focus:bg-slate-800/60 rounded px-1 py-0.5 text-sm font-black text-white outline-none transition w-36"
              />
              {/* الاسم العربي — قابل للتعديل */}
              <input
                value={draft.name_ar}
                onChange={(e) => edit({ name_ar: e.target.value })}
                placeholder="الاسم العربي"
                dir="rtl"
                className="bg-transparent border-b border-transparent hover:border-slate-600 focus:border-teal-500 focus:bg-slate-800/60 rounded px-1 py-0.5 text-sm font-bold text-teal-300 outline-none transition w-32"
              />
              <span className="text-[9px] font-black uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full">{agent.pipeline_type}</span>
              <span className="text-[9px] font-mono text-slate-600">#{agent.key}</span>
            </div>
            {/* الدور — قابل للتعديل */}
            <input
              value={draft.role}
              onChange={(e) => edit({ role: e.target.value })}
              placeholder="Role / responsibility"
              className="mt-1 bg-transparent text-xs text-slate-400 outline-none border-b border-transparent hover:border-slate-600 focus:border-teal-500 rounded px-1 py-0.5 w-full max-w-md transition"
            />
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {saved && <span className="text-[10px] font-black uppercase tracking-wider text-emerald-400">Saved ✓</span>}
          {saving && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
          <button
            onClick={() => setShowPrompt(!showPrompt)}
            title="فتح برومبت التدريب"
            className={`flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border transition ${
              showPrompt ? 'bg-slate-800 text-white border-slate-600' : 'border-slate-600 text-slate-300 hover:bg-slate-800'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" /> التدريب
          </button>
          <button
            onClick={() => preview.toggle()}
            disabled={preview.loading}
            title="تجربة حية للوكيل بالتعديلات الحالية (دون حفظ)"
            className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider px-3 py-1.5 rounded-lg border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 disabled:opacity-50 transition"
          >
            {preview.loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            تجربة
          </button>
          <button
            onClick={() => onSave({ enabled: !agent.enabled })}
            title={agent.enabled ? 'تعطيل الوكيل من السرب' : 'تفعيل الوكيل'}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition shrink-0 ${agent.enabled ? 'bg-emerald-500' : 'bg-slate-700'}`}
            aria-label="Toggle agent"
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${agent.enabled ? 'translate-x-6' : 'translate-x-1'}`} />
          </button>
        </div>
      </div>

      {/* Model binding row */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        <label className="block">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">LLM Provider</span>
          <select value={draft.provider_id ?? ''}
            onChange={(e) => edit({ provider_id: e.target.value ? Number(e.target.value) : null })}
            className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-teal-500">
            <option value="">— platform default —</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.provider_type})</option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Model Override</span>
          <input value={draft.model_override}
            onChange={(e) => edit({ model_override: e.target.value })}
            placeholder="e.g. qwen2.5:14b"
            className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-teal-500" />
        </label>
        <label className="block">
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Temperature — {draft.temperature.toFixed(2)}</span>
          <input type="range" min={0} max={1} step={0.05} value={draft.temperature}
            onChange={(e) => edit({ temperature: Number(e.target.value) })}
            className="mt-3 w-full accent-teal-500" />
        </label>
      </div>

      {/* Save bar */}
      {dirty && (
        <div className="mt-3 flex items-center justify-end gap-2">
          <button onClick={() => { setDraft(draftFrom(agent)); setDirty(false); }}
            className="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-300 hover:bg-slate-800">
            تراجع
          </button>
          <button onClick={handleSave} disabled={saving}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-black uppercase tracking-wider bg-gradient-to-r from-teal-500 to-blue-600 text-white shadow disabled:opacity-50">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
            حفظ التعديلات
          </button>
        </div>
      )}

      {/* Training prompt editor */}
      {showPrompt && (
        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950/60 p-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-teal-400" /> برومبت التدريب (System Prompt) — شخصية الوكيل وقواعده
          </p>
          <textarea
            value={draft.system_prompt}
            onChange={(e) => edit({ system_prompt: e.target.value })}
            rows={7}
            dir="auto"
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-teal-500 resize-y"
          />
          <p className="mt-2 text-[10px] text-slate-500">
            اكتب للوكيل هويته: من هو، وماذا يفعل بدقة، وكيف يجيب، وما يجب ألا يفعله أبداً. يُحفظ مع بقية التعديلات.
          </p>
        </div>
      )}

      {/* Live preview */}
      {preview.active && (
        <div className="mt-4 rounded-lg border border-cyan-500/30 bg-cyan-500/5 p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-black uppercase tracking-widest text-cyan-300 flex items-center gap-1.5">
              <Play className="h-3 w-3" /> معاينة حية — {preview.repliedAs || '…'}
              {preview.model && <span className="font-mono text-cyan-600 normal-case">· {preview.model}</span>}
            </p>
            <button onClick={() => preview.toggle()} className="p-1 rounded text-slate-400 hover:text-white"><X className="h-3.5 w-3.5" /></button>
          </div>
          <textarea
            value={preview.message}
            onChange={(e) => preview.setMessage(e.target.value)}
            rows={2}
            placeholder="اكتب رسالة اختبار للوكيل…"
            dir="auto"
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500 resize-y"
          />
          <div className="flex gap-2 mt-2">
            <textarea
              value={preview.sampleContext}
              onChange={(e) => preview.setSampleContext(e.target.value)}
              rows={2}
              placeholder="سياق اختياري من مستندات المنافسة ليختبر عليه الوكيل…"
              dir="auto"
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-400 focus:outline-none focus:border-cyan-500 resize-y"
            />
            <button onClick={preview.run} disabled={preview.loading || !preview.message.trim()}
              className="self-stretch px-4 rounded-lg text-xs font-black uppercase tracking-wider bg-cyan-600 text-white hover:bg-cyan-500 disabled:opacity-40">
              {preview.loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Run'}
            </button>
          </div>
          {preview.reply && (
            <div className="mt-3 rounded-lg bg-slate-900 border border-slate-700 p-3">
              <p className="whitespace-pre-wrap text-sm text-slate-200 leading-relaxed" dir="auto">{preview.reply}</p>
            </div>
          )}
          {preview.error && (
            <p className="mt-2 text-xs text-rose-300 font-semibold">{preview.error}</p>
          )}
        </div>
      )}
    </div>
  );
}

/** خطاف معاينة حية — يستدعي POST /agents/{key}/preview بالمسودة الحالية دون حفظ. */
function useAgentPreview(agent: AgentEntry, draft: AgentDraft) {
  const [active, setActive] = useState(false);
  const [message, setMessage] = useState('عرّف بنفسك بدورك في هذه المنصة في سطرين.');
  const [sampleContext, setSampleContext] = useState('');
  const [reply, setReply] = useState('');
  const [repliedAs, setRepliedAs] = useState('');
  const [model, setModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    if (!message.trim() || loading) return;
    setLoading(true);
    setError('');
    setReply('');
    try {
      const res = await fetch(`${API}/api/v1/agents/${agent.key}/preview`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft, message, sample_context: sampleContext }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setReply(data.reply || '');
      setRepliedAs(data.replied_as || '');
      setModel(data.model || '');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'فشلت المعاينة');
    } finally {
      setLoading(false);
    }
  };

  return {
    active, setActive, message, setMessage, sampleContext, setSampleContext,
    reply, repliedAs, model, loading, error, run,
    toggle: () => setActive((v) => !v),
  };
}

/* ============================ Add provider ============================ */

function AddProviderModal(props: {
  form: typeof ADD_FORM_DEFAULT;
  setForm: (f: typeof ADD_FORM_DEFAULT) => void;
  onClose: () => void;
  onSubmit: () => void;
}) {
  const { form, setForm, onClose, onSubmit } = props;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-xl bg-slate-900 rounded-2xl shadow-2xl overflow-hidden border border-slate-700">
        <div className="px-6 py-4 border-b border-slate-700 bg-slate-900">
          <h2 className="text-lg font-bold text-white flex items-center gap-2"><PlugZap className="h-5 w-5 text-teal-400" /> Add LLM Provider</h2>
          <p className="text-xs text-slate-400 mt-0.5">Cloud APIs or local Ollama / LM Studio — encrypted at rest.</p>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Display Name</span>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Ollama — Llama 3.1" className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" />
            </label>
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Provider Type</span>
              <select value={form.provider_type}
                onChange={(e) => {
                  const type = e.target.value as ProviderType;
                  setForm({ ...form, provider_type: type, base_url: PROVIDER_META[type].defaultUrl });
                }}
                className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                {Object.entries(PROVIDER_META).map(([key, meta]) => (
                  <option key={key} value={key}>{meta.label}{meta.privacy ? ' · 🔒 local' : ''}</option>
                ))}
              </select>
            </label>
            <label className="block md:col-span-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Base URL</span>
              <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" />
            </label>
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Chat Model</span>
              <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} placeholder="llama3.1:8b / gpt-4o-mini" className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" />
            </label>
            <label className="block">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">Embedding Model (RAG)</span>
              <input value={form.embedding_model} onChange={(e) => setForm({ ...form, embedding_model: e.target.value })} placeholder="nomic-embed-text" className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" />
            </label>
            <label className="block md:col-span-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-1"><Lock className="h-3 w-3" /> API Key (encrypted at rest)</span>
              <input value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} placeholder="sk-… (empty for local providers)" type="password" className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" />
            </label>
          </div>
          <div className="flex items-center justify-end gap-2 pt-1">
            <button onClick={onClose} className="px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800 rounded-lg">Cancel</button>
            <button onClick={onSubmit} disabled={!form.name}
              className="px-4 py-2 rounded-lg text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-blue-600 disabled:opacity-40">
              Add & Enable
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
