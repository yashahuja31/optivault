const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  token: string | null,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(body.detail || `Request failed (${res.status})`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// --- Types matching the backend schemas ---
export interface CloudAccount {
  id: string;
  provider: string;
  bucket_name: string;
  created_at: string;
}

export interface ScanJob {
  id: string;
  account_id: string;
  status: "pending" | "running" | "completed" | "failed";
  objects_scanned: number;
  error_message?: string | null;
}

export interface AnalysisResult {
  total_files: number;
  current_monthly_cost_usd: number;
  estimated_monthly_savings_usd: number;
  duplicate_files: number;
  duplicate_waste_usd: number;
  stale_files: number;
  wrong_tier_files: number;
  archive_candidates: number;
  archive_savings_usd: number;
  compression_candidates: number;
}

export interface OptimizationReportOut {
  id: string;
  total_savings_usd: number;
  summary_text: string;
  created_at: string;
}

// --- Cloud accounts ---
// Each call takes an Auth0 access token (from getAccessTokenSilently()).
export function listAccounts(token: string) {
  return request<CloudAccount[]>("/cloud-accounts", token);
}

export function createAccount(token: string, bucket_name: string) {
  return request<CloudAccount>("/cloud-accounts", token, {
    method: "POST",
    body: JSON.stringify({ bucket_name }),
  });
}

export function startScan(token: string, accountId: string) {
  return request<ScanJob>(`/cloud-accounts/${accountId}/scan`, token, { method: "POST" });
}

export function getScanStatus(token: string, accountId: string) {
  return request<ScanJob>(`/cloud-accounts/${accountId}/scan-status`, token);
}

export function analyzeAccount(token: string, accountId: string) {
  return request<AnalysisResult>(`/cloud-accounts/${accountId}/analyze`, token, {
    method: "POST",
  });
}

export function getReport(token: string, accountId: string) {
  return request<OptimizationReportOut>(`/cloud-accounts/${accountId}/report`, token);
}

export { ApiError };
