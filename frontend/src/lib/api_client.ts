import { TenantContext } from './demoData';

export const API_BASE = 'http://localhost:8000';

/**
 * Demo-dev JWT signing secret. Mirrors app/core/security.py (SECRET_KEY default)
 * and the inline verify_token used by the audit endpoints. Used ONLY to mint a
 * valid demo session token for the active workspace so the dashboard can drive
 * the real authenticated audit APIs without a login flow.
 */
const DEV_JWT_SECRET = 'supersecretkey_for_dev_only';
const TOKEN_TTL_SECONDS = 3600;

interface TokenCache {
  tenantId: string;
  token: string;
  expiresAt: number;
}

let tokenCache: TokenCache | null = null;

function b64u(input: string): string {
  return btoa(input).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function hmacSha256(message: string, secret: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const signature = await crypto.subtle.sign('HMAC', key, enc.encode(message));
  return b64u(String.fromCharCode(...new Uint8Array(signature)));
}

/**
 * Mints (or reuses a cached) valid demo HS256 JWT scoped to the active workspace.
 * Role is pinned to `lead_architect` so it satisfies the backend RBAC gate.
 */
export async function getDemoToken(tenant: TenantContext): Promise<string> {
  if (tokenCache && tokenCache.tenantId === tenant.id && tokenCache.expiresAt > Date.now()) {
    return tokenCache.token;
  }

  const header = b64u(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const now = Math.floor(Date.now() / 1000);
  const payload = b64u(
    JSON.stringify({
      sub: tenant.id,
      role: 'lead_architect',
      workspace: tenant.name,
      project: tenant.project,
      tenant_id: tenant.id,
      iat: now,
      exp: now + TOKEN_TTL_SECONDS,
    }),
  );
  const signingInput = `${header}.${payload}`;
  const signature = await hmacSha256(signingInput, DEV_JWT_SECRET);
  const token = `${signingInput}.${signature}`;

  tokenCache = { tenantId: tenant.id, token, expiresAt: now + TOKEN_TTL_SECONDS };
  return token;
}

/**
 * Auth session interceptor — attaches `Authorization: Bearer <demo JWT>` for the
 * active workspace to every audit request so FastAPI security middleware passes.
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {},
  tenant?: TenantContext,
): Promise<Response> {
  const token = tenant ? await getDemoToken(tenant) : null;
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  return fetch(`${API_BASE}${path}`, { ...options, headers });
}

export interface AuditTriggerResult {
  tender_id: number;
  status: string;
  message?: string;
}

export interface TenderStatusResult {
  tender_id: number;
  title: string;
  client_name: string;
  status: string;
  technical_score: number | null;
  audit_metadata: Record<string, unknown>;
  records: Array<Record<string, unknown>>;
}

/**
 * Dispatches the uploaded tender package (RFP/BOQ/IFC files + XER schedule) to
 * POST /api/v1/audits/trigger with the active workspace Bearer token attached.
 */
export async function triggerTenderAudit(
  files: File[],
  tenant: TenantContext,
): Promise<AuditTriggerResult> {
  const formData = new FormData();
  const schedule = files.find((f) => f.name.toLowerCase().endsWith('.xer')) || files[0];
  const rfpFiles = files.filter((f) => f.name.toLowerCase().endsWith('.xer') === false);

  if (rfpFiles.length === 0) {
    formData.append('rfp_files', files[0]);
  } else {
    rfpFiles.forEach((f) => formData.append('rfp_files', f));
  }
  formData.append('schedule_file', schedule);

  const res = await apiFetch('/api/v1/audits/trigger', { method: 'POST', body: formData }, tenant);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = body.detail;
    } catch {
      /* keep status fallback */
    }
    throw new Error(detail);
  }
  return res.json();
}

/** Authenticated status poll for a tender audit. */
export async function fetchTenderStatus(
  tenderId: number,
  tenant: TenantContext,
): Promise<TenderStatusResult | null> {
  const res = await apiFetch(`/api/v1/audits/${tenderId}`, {}, tenant);
  if (!res.ok) return null;
  return res.json();
}