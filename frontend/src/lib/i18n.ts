"use client";

/**
 * i18n — نظام التعريب الثنائي (عربي/إنجليزي).
 * - اللغة محفوظة في localStorage وتطبَّق فوراً على كل المنصة.
 * - dir يتقلب تلقائياً (rtl/ltr) مع اللغة.
 * - إضافة نص جديد: أضفه للمفتاحين معاً واستخدمه عبر t("key").
 */

export type Lang = "ar" | "en";

const STORAGE_KEY = "contech.lang";

const DICT = {
  // ---------- Header / عام ----------
  appName: { ar: "ConTech AI Platform", en: "ConTech AI Platform" },
  tagline: { ar: "ذكاء المنافسات متعدد الوكلاء", en: "Multi-Agent Tender Intelligence" },
  leadArchitect: { ar: "المهندس الرئيسي", en: "Lead Architect" },
  uploadTenderPackage: { ar: "رفع كراسة المنافسة", en: "Upload Tender Package" },
  startFresh: { ar: "بدء من جديد", en: "Start Fresh" },
  startFreshHint: {
    ar: "جلسة جديدة: يُزال سياق المنافسة الحالية من الشاشة (البيانات والمشاريع تبقى محفوظة)",
    en: "Fresh session: clears current workspace context (all data and projects stay saved)",
  },
  settings: { ar: "الإعدادات", en: "Settings" },
  language: { ar: "English", en: "العربية" },

  // ---------- Document Library ----------
  docLibrary: { ar: "مكتبة المستندات والاستيعاب", en: "Document Library & Ingestion" },
  files: { ar: "ملفات", en: "files" },
  processed: { ar: "معالج", en: "processed" },
  criteria: { ar: "معايير", en: "criteria" },
  proposal: { ar: "عرض", en: "proposal" },
  processingBg: { ar: "قيد المعالجة في الخلفية…", en: "processing in background…" },
  scanServerFolder: { ar: "مسح مجلد على الخادم", en: "Scan Server Folder" },
  scanServerHint: {
    ar: "يسجل ملفات مجلد موجود على الخادم دون نسخها — للكراسات الضخمة",
    en: "Registers files from a server-side folder without copying — for huge packages",
  },
  uploadProposal: { ar: "رفع العرض الفني", en: "Upload Proposal" },
  uploadProposalHint: {
    ar: "ارفع العرض الفني لفريقك — يُوسم PROPOSAL حصراً ويظهر زر التقييم",
    en: "Upload your team's technical proposal — tagged PROPOSAL, enables evaluation",
  },
  uploadFiles: { ar: "رفع ملفات الكراسة", en: "Upload Files" },
  uploadFilesHint: {
    ar: "أضف ملفات كراسة المنافسة أو ملاحقها — تُضاف للقائمة دون تشغيل السرب",
    en: "Add RFP package files or addenda — added to library without launching the swarm",
  },
  noDocs: { ar: "لا توجد مستندات بعد لهذه المنافسة.", en: "No documents ingested yet for this tender." },
  noDocsHint: {
    ar: "ارفع كراسة المنافسة (RFP/معايير/مواصفات) — وملف العرض الفني لاحقاً ليظهر زر التقييم.",
    en: "Upload the tender package (RFP/criteria/specs) — then the proposal to unlock evaluation.",
  },
  askCorpus: { ar: "اسأل كراسة المنافسة — الإجابة تستشهد الملف والصفحة", en: "Ask the RFP Corpus — answers cite file & page" },
  askPlaceholder: { ar: "مثال: أين شرط الخرسانة المسلحة؟", en: "e.g. Where is the dewatering requirement?" },

  // ---------- Proposal evaluation ----------
  proposalEvalTitle: { ar: "تقييم العرض الفني ضد معايير المنافسة", en: "Evaluate Proposal vs Competition Criteria" },
  evaluateProposal: { ar: "قيّم العرض الفني", en: "Evaluate Proposal" },
  strengths: { ar: "نقاط القوة", en: "Strengths" },
  weaknesses: { ar: "نقاط الضعف", en: "Weaknesses" },
  partialCoverage: { ar: "تغطية جزئية (تحتاج تعميقاً)", en: "Partial coverage (needs depth)" },
  noGaps: { ar: "لا فجوات — العرض يغطي كل البنود ✓", en: "No gaps — proposal covers all mandates ✓" },
  noFull: { ar: "لا توجد تغطية كاملة — راجع نقاط الضعف.", en: "No full coverage — review weaknesses." },
  proposalEvalHint: {
    ar: "يحلل العرض الفني ويقارنه بمعايير التقييم: نقاط القوة والضعف والدرجة",
    en: "Analyzes the technical proposal against criteria: strengths, weaknesses & score",
  },
  mandatesAddressed: { ar: "البنود المجابة", en: "Mandates addressed" },

  // ---------- Upload modal ----------
  uploadModalTitle: { ar: "رفع كراسة المنافسة", en: "Upload Tender Package" },
  uploadModalHint: {
    ar: "يرفع الكراسة ويشعل سرب الوكلاء فوراً — للبداية السريعة",
    en: "Uploads the package and launches the swarm immediately — quick start",
  },
  authenticatedWs: { ar: "مساحة عمل موثقة", en: "Authenticated workspace" },
  dropHere: { ar: "اسحب كراسة المنافسة هنا أو", en: "Drag & drop your tender package, or" },
  browse: { ar: "تصفح", en: "browse" },
  cancel: { ar: "إلغاء", en: "Cancel" },
  runFullAudit: { ar: "شغّل التدقيق الكامل", en: "Run Full-Stack Audit" },
  ingesting: { ar: "جارٍ الاستيعاب…", en: "Ingesting…" },
  unsupportedFiles: { ar: "ملفات غير مدعومة تم تخطيها", en: "Skipped unsupported file(s)" },

  // ---------- Swarm ----------
  swarmTitle: { ar: "تنسيق سرب الوكلاء", en: "Multi-Agent Swarm Orchestration" },
  swarmHint: { ar: "خط أنابيب LangGraph — انقر أي وكيل لتفاصيله", en: "LangGraph agent pipeline — click any node for detail" },
  launchSwarm: { ar: "انطلق أيها الوكلاء", en: "Launch Agents" },
  swarmRunning: { ar: "السرب يعمل…", en: "Swarm Running…" },
  launching: { ar: "جارٍ الإطلاق…", en: "Launching…" },
  liveSse: { ar: "بث حي", en: "Live SSE" },

  // ---------- Studios ----------
  commandCenter: { ar: "مركز القيادة", en: "Command Center" },
  studioWorkspaces: { ar: "استوديوهات العمل", en: "Studio Workspaces" },
  draftingAssistant: { ar: "مساعد صياغة العرض", en: "Proposal Drafting Assistant" },
  llmEnrich: { ar: "إثراء بالذكاء", en: "LLM Enrich" },
  regenerate: { ar: "إعادة التوليد", en: "Regenerate" },

  // ---------- Settings ----------
  platformSettings: { ar: "إعدادات المنصة", en: "Platform Settings" },
  agentRegistry: { ar: "سجل الوكلاء والتدريب", en: "Agent Registry & Training" },
  llmProviders: { ar: "مزودو الذكاء", en: "LLM Providers" },
  training: { ar: "التدريب", en: "Training" },
  tryIt: { ar: "تجربة", en: "Try" },
  livePreview: { ar: "معاينة حية", en: "Live preview" },
  run: { ar: "تشغيل", en: "Run" },
  saveChanges: { ar: "حفظ التعديلات", en: "Save changes" },
  revert: { ar: "تراجع", en: "Revert" },
  addProvider: { ar: "إضافة مزود", en: "Add Provider" },
  test: { ar: "اختبار", en: "Test" },
  delete: { ar: "حذف", en: "Delete" },

  // ---------- Sections ----------
  documentLibrary: { ar: "مكتبة المستندات والاستيعاب", en: "Document Library & Ingestion" },
  auditComplete: { ar: "اكتمل التدقيق — درجة الامتثال الفني", en: "Audit complete — technical compliance score" },
  swarmCanvasTitle: { ar: "لوحة السرب (تقنية)", en: "Swarm Canvas (technical)" },
  portfolioLive: { ar: "محفظة المنافسات — حية", en: "Tender Portfolio — Live" },
  systemTelemetry: { ar: "قياسات النظام والنشاط", en: "System Telemetry & Activity" },
  computedFromData: { ar: "محسوبة من بياناتك", en: "computed from your data" },
  totalTenders: { ar: "إجمالي المنافسات", en: "Total Tenders" },
  avgTechScore: { ar: "متوسط الدرجة الفنية", en: "Avg Technical Score" },
  docsIngested: { ar: "مستندات مستوعبة", en: "Documents Ingested" },
  criticalGaps: { ar: "فجوات حرجة", en: "Critical Gaps" },
  clusterStatus: { ar: "حالة النظام", en: "Cluster Status" },
  activeAgents: { ar: "الوكلاء النشطون", en: "Active Agents" },
  swarmsRun: { ar: "مرات تشغيل السرب", en: "Swarms Run" },
  providersOn: { ar: "مزودو الذكاء المفعّلون", en: "LLM Providers On" },
  recentAuditActivity: { ar: "أحدث نشاط تدقيق — حي من قاعدة البيانات", en: "Recent Audit Activity — live from database" },
  complianceDistribution: { ar: "توزيع أحكام الامتثال", en: "Compliance Verdict Distribution" },
  noAuditYet: { ar: "لا نتائج تدقيق بعد — أطلق السرب على منافسة لتعبئة هذا الرسم.", en: "No audit results yet — launch the swarm on a tender to populate this chart." },
  noActivity: { ar: "لا نشاط بعد.", en: "No activity yet." },
  studioWorkspacesTitle: { ar: "استوديوهات العمل", en: "Studio Workspaces" },
  studioHint: { ar: "استوديوهات هندسية وتجارية وميدانية مدفوعة بالوكلاء", en: "Agent-driven engineering, commercial & field operations studios" },

  // ---------- Document statuses/categories ----------
  catEvaluation: { ar: "معايير التقييم", en: "Evaluation Criteria" },
  catSpecs: { ar: "المواصفات", en: "Specifications" },
  catBoq: { ar: "جدول الكميات", en: "BOQ" },
  catDrawings: { ar: "المخططات", en: "Drawings / CAD" },
  catForms: { ar: "النماذج", en: "Forms" },
  catAddendum: { ar: "ملحق", en: "Addendum" },
  catContract: { ar: "العقد", en: "Contract" },
  catProposal: { ar: "عرضنا الفني", en: "Our Proposal" },
  catOther: { ar: "أخرى", en: "Other" },
  statusProcessed: { ar: "معالَج", en: "PROCESSED" },
  statusProcessing: { ar: "قيد المعالجة…", en: "PROCESSING…" },
  statusRegistered: { ar: "مسجَّل", en: "REGISTERED" },
  statusFailed: { ar: "فشل", en: "FAILED" },
  pinnedGate: { ar: "معيار مثبّت", en: "Pinned Gate" },
  pinAction: { ar: "تثبيت", en: "Pin" },
} as const;

export type DictKey = keyof typeof DICT;

export function getLang(): Lang {
  if (typeof window === "undefined") return "ar";
  return (localStorage.getItem(STORAGE_KEY) as Lang) || "ar";
}

export function setLang(lang: Lang) {
  localStorage.setItem(STORAGE_KEY, lang);
  // إعادة التحميل تطبّق dir واللغة على كل المكونات دون حالة معقدة
  window.dispatchEvent(new CustomEvent("contech.lang-changed", { detail: lang }));
}

export function t(key: DictKey, lang?: Lang): string {
  const l = lang || getLang();
  return DICT[key][l];
}

export function isRTL(lang?: Lang): boolean {
  return (lang || getLang()) === "ar";
}
