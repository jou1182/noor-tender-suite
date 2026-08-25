/**
 * Platform analytics — mirrors GET /api/v1/analytics/overview.
 * كل الأرقام تُحسب من قاعدة البيانات الفعلية (لا mock).
 */

export interface PlatformOverview {
  portfolio: {
    tenders_total: number;
    tenders_completed: number;
    tenders_processing: number;
    tenders_draft: number;
    documents_ingested: number;
    compliance_records: number;
    avg_technical_score: number | null;
    scored_tenders: number;
  };
  system: {
    agents_enabled: number;
    providers_enabled: number;
    last_audit_log_id: number | null;
    cluster_status: string;
  };
  compliance_distribution: Record<string, number>;
  recent_activity: Array<{
    id: number;
    action: string;
    tender_id: number | null;
    user: string;
    at: string;
  }>;
}

export async function fetchPlatformOverview(): Promise<PlatformOverview | null> {
  try {
    const res = await fetch('http://localhost:8000/api/v1/analytics/overview');
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
