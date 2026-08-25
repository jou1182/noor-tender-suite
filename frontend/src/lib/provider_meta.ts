/**
 * Add-provider form defaults — shared between the settings page and any
 * future provider onboarding UI. Exported from lib so page files keep
 * exporting only what Next.js App Router allows.
 */
import type { ProviderType } from '../types/platform';

export const PROVIDER_META: Record<ProviderType, { label: string; defaultUrl: string; privacy: boolean }> = {
  openai: { label: 'OpenAI (GPT)', defaultUrl: 'https://api.openai.com/v1', privacy: false },
  anthropic: { label: 'Anthropic (Claude)', defaultUrl: 'https://api.anthropic.com', privacy: false },
  google: { label: 'Google (Gemini)', defaultUrl: 'https://generativelanguage.googleapis.com', privacy: false },
  deepseek: { label: 'DeepSeek', defaultUrl: 'https://api.deepseek.com/v1', privacy: false },
  ollama: { label: 'Ollama (Local)', defaultUrl: 'http://localhost:11434/v1', privacy: true },
  lmstudio: { label: 'LM Studio (Local)', defaultUrl: 'http://localhost:1234/v1', privacy: true },
};

export const ADD_FORM_DEFAULT = {
  name: '', provider_type: 'ollama' as ProviderType,
  base_url: PROVIDER_META.ollama.defaultUrl, model: '', api_key: '', embedding_model: '',
};
