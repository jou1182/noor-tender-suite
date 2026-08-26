/**
 * Tenders API — dynamic workspace lifecycle (list / create / rename / delete / launch).
 * يغذي القائمة العلوية الديناميكية وزر إطلاق السرب والحذف الآمن.
 */
import { API_BASE } from './api_client';

export interface TenderSummary {
  id: number;
  title: string;
  client_name: string;
  status: string;
  technical_score: number | null;
  created_at: string;
  document_count: number;
}

export async function listTenders(): Promise<TenderSummary[]> {
  const res = await fetch(`${API_BASE}/api/v1/tenders`);
  if (!res.ok) throw new Error(`Failed to list tenders (HTTP ${res.status})`);
  const data = await res.json();
  return data.tenders || [];
}

export async function createTender(title: string, clientName: string): Promise<TenderSummary> {
  const res = await fetch(`${API_BASE}/api/v1/tenders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, client_name: clientName }),
  });
  if (!res.ok) throw new Error(`Failed to create tender (HTTP ${res.status})`);
  return res.json();
}

export async function renameTender(id: number, patch: { title?: string; client_name?: string }): Promise<TenderSummary> {
  const res = await fetch(`${API_BASE}/api/v1/tenders/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error(`Failed to update tender (HTTP ${res.status})`);
  return res.json();
}

/** يحذف المنافسة وكل ما يرتبط بها نهائياً — يجب أن يكون المستخدم قد أكّد في الواجهة. */
export async function deleteTender(id: number): Promise<void> {
  const res = await fetch(`${API_BASE}/api/v1/tenders/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to delete tender (HTTP ${res.status})`);
}

/** زر «انطلق أيها الوكلاء» — يشعل السرب على منافسة موجودة. */
export async function launchTenderSwarm(
  id: number,
): Promise<{ tender_id: number; status: string; message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/tenders/${id}/launch`, { method: 'POST' });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `Failed to launch swarm (HTTP ${res.status})`);
  return body;
}


/** رفع دفعة ملفات كراسة إلى منافسة قائمة (عبر نقطة documents/upload لكل ملف). */
export async function uploadTenderFiles(tenderId: number, files: File[], hasXer: boolean): Promise<void> {
  for (const file of files) {
    const form = new FormData();
    form.append("file", file);
    const isXer = file.name.toLowerCase().endsWith(".xer");
    // XER يمر عبر مسار الجدول الزمني في audits/trigger لاحقاً؛ هنا نسجله كمستند
    const res = await fetch(`${API_BASE}/api/v1/documents/upload?tender_id=${tenderId}${isXer ? "&doc_category=SCHEDULE" : ""}`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `فشل رفع ${file.name}`);
    }
  }
}