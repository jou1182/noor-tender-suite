"""Provider templates — قوالب المزودين الجاهزة.

تغذي واجهة إضافة مزود جديد: المستخدم يختار قالباً فيُملأ Base URL
والنوع تلقائياً — ويبقى فقط إدخال مفتاح API واختيار الموديل.
أي مزود جديد عالمياً = إضافة سطر هنا (أو اختيار «مخصص» من الواجهة).
"""

from typing import Any, Dict, List

# بروتوكولات البوابة المدعومة (تطابق PROVIDER_ADAPTERS في llm_gateway_v2)
PROTOCOLS = ("openai_compatible", "anthropic", "google", "ollama")

# أنواع legacy المدعومة للتوافق مع البيانات القائمة
LEGACY_TYPES = ("openai", "deepseek", "ollama", "lmstudio", "anthropic", "google")

TEMPLATES: List[Dict[str, Any]] = [
    # ---------- محلي (خصوصية كاملة) ----------
    {
        "key": "ollama",
        "name": "Ollama (محلي)",
        "provider_type": "ollama",
        "base_url": "http://host.docker.internal:11434/v1",
        "privacy_safe": True,
        "needs_key": False,
        "hint": "مجاني ومحلي 100% — البيانات لا تخرج من جهازك. الموديلات: qwen3:4b (موصى به)، qwen3:8b.",
        "models_hint": "qwen3:4b",
    },
    {
        "key": "lmstudio",
        "name": "LM Studio (محلي)",
        "provider_type": "lmstudio",
        "base_url": "http://host.docker.internal:1234/v1",
        "privacy_safe": True,
        "needs_key": False,
        "hint": "خادم محلي من تطبيق LM Studio — فعّل الخادم من التطبيق أولاً.",
        "models_hint": "حسب ما حمّلته في التطبيق",
    },
    # ---------- سحابيون بروتوكول OpenAI ----------
    {
        "key": "openai",
        "name": "OpenAI (GPT)",
        "provider_type": "openai",
        "base_url": "https://api.openai.com/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "الأقوى عموماً. الموديلات: gpt-4o-mini (اقتصادي)، gpt-4o (متقدم).",
        "models_hint": "gpt-4o-mini",
    },
    {
        "key": "deepseek",
        "name": "DeepSeek",
        "provider_type": "deepseek",
        "base_url": "https://api.deepseek.com/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "أرخص بديل عالمي بجودة قوية — ممتاز للعربية. الموديلات: deepseek-chat، deepseek-reasoner.",
        "models_hint": "deepseek-chat",
    },
    {
        "key": "groq",
        "name": "Groq",
        "provider_type": "openai_compatible",
        "base_url": "https://api.groq.com/openai/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "الأسرع عالمياً (أجهزة LPU) — له حصة مجانية سخية. الموديلات: llama-3.3-70b-versatile، qwen-2.5-32b.",
        "models_hint": "llama-3.3-70b-versatile",
    },
    {
        "key": "openrouter",
        "name": "OpenRouter",
        "provider_type": "openai_compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "بوابة موحدة لأكثر من 200 موديل (GPT وClaude وGemma...) بمفتاح واحد — الأفضل للتجربة والمقارنة.",
        "models_hint": "openai/gpt-4o-mini أو anthropic/claude-3.5-sonnet",
    },
    {
        "key": "together",
        "name": "Together AI",
        "provider_type": "openai_compatible",
        "base_url": "https://api.together.xyz/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "موديلات مفتوحة المصدر مستضافة بأسعار منافسة (Llama, Qwen, Mixtral).",
        "models_hint": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    },
    {
        "key": "mistral",
        "name": "Mistral AI",
        "provider_type": "openai_compatible",
        "base_url": "https://api.mistral.ai/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "أوروبي، جودة/سعر ممتازة، ودعم جيد للغات المتعددة.",
        "models_hint": "mistral-large-latest",
    },
    {
        "key": "fireworks",
        "name": "Fireworks AI",
        "provider_type": "openai_compatible",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "استدلال فائق السرعة للموديلات المفتوحة.",
        "models_hint": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    },
    # ---------- سحابيون ببروتوكولات خاصة ----------
    {
        "key": "anthropic",
        "name": "Anthropic (Claude)",
        "provider_type": "anthropic",
        "base_url": "https://api.anthropic.com",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "الأفضل في التحليل الطويل والالتزام بالتعليمات. الموديلات: claude-sonnet-4-5، claude-haiku-4-5.",
        "models_hint": "claude-sonnet-4-5",
    },
    {
        "key": "google",
        "name": "Google (Gemini)",
        "provider_type": "google",
        "base_url": "https://generativelanguage.googleapis.com",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "نافذة سياق ضخمة (مليون token) — ممتاز لكراسات الشروط الضخمة. gemini-2.5-flash اقتصادي.",
        "models_hint": "gemini-2.5-flash",
    },
    # ---------- قالب مخصص ----------
    {
        "key": "custom",
        "name": "مزود مخصص (Custom)",
        "provider_type": "openai_compatible",
        "base_url": "",
        "privacy_safe": False,
        "needs_key": True,
        "hint": "أي خدمة متوافقة مع بروتوكول OpenAI (vLLM، LiteLLM، خادم داخلي...) — أدخل Base URL الخاص بها.",
        "models_hint": "اسم الموديل لدى مزودك",
    },
]


def list_templates() -> List[Dict[str, Any]]:
    return TEMPLATES


def find_template(key: str) -> Dict[str, Any] | None:
    for t in TEMPLATES:
        if t["key"] == key:
            return t
    return None
