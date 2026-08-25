/**
 * Platform types — LLM providers, agent registry & document intelligence.
 * Mirrors app/models/platform_models.py + API serializers.
 */

export type ProviderType = 'openai' | 'anthropic' | 'google' | 'deepseek' | 'ollama' | 'lmstudio';

export interface LLMProvider {
  id: number;
  name: string;
  provider_type: ProviderType;
  base_url: string;
  model: string;
  embedding_model: string;
  enabled: boolean;
  is_default: boolean;
  privacy_safe: boolean;
  api_key_masked: string;
  has_api_key: boolean;
}

export interface ConnectionTestResult {
  ok: boolean;
  latency_ms: number;
  models: string[];
  error?: string;
}

export interface AgentEntry {
  id: number;
  key: string;
  name_ar: string;
  name_en: string;
  avatar_emoji: string;
  role: string;
  pipeline_type: 'technical' | 'financial' | 'drafting' | 'shared';
  system_prompt: string;
  provider_id: number | null;
  provider_name: string | null;
  model_override: string;
  temperature: number;
  enabled: boolean;
  execution_order: number;
}

export type DocumentCategory =
  | 'EVALUATION_CRITERIA' | 'SPECIFICATIONS' | 'BOQ' | 'DRAWINGS'
  | 'FORMS' | 'ADDENDUM' | 'CONTRACT' | 'OTHER';

export type DocumentStatus = 'REGISTERED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';

export interface TenderDocumentItem {
  id: number;
  tender_id: number;
  filename: string;
  size_bytes: number;
  file_ext: string;
  doc_category: DocumentCategory;
  classification_confidence: number;
  status: DocumentStatus;
  process_error: string;
  page_count: number;
  text_chars: number;
  ocr_used: boolean;
  chunk_count: number;
  is_pinned_criteria: boolean;
  uploaded_at: string;
  text_sample: string;
}

export interface TenderRequirementItem {
  id: number;
  requirement_type: 'MANDATORY' | 'WEIGHTED' | 'DISQUALIFICATION';
  requirement_text: string;
  weight: number | null;
  clause_ref: string;
}

export interface RagCitation {
  filename: string;
  page: number;
  text: string;
  score: number;
  via: 'vector' | 'keyword';
}