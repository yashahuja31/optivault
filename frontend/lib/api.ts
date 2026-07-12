const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "optivault_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof URLSearchParams)) {
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

// --- Auth ---
export async function signup(email: string, password: string) {
  const data = await request<{ access_token: string }>("/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password });
  const data = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body,
  });
  setToken(data.access_token);
  return data;
}

// --- Cloud accounts ---
export function listAccounts() {
  return request<CloudAccount[]>("/cloud-accounts");
}

export function createAccount(bucket_name: string) {
  return request<CloudAccount>("/cloud-accounts", {
    method: "POST",
    body: JSON.stringify({ bucket_name }),
  });
}

export function startScan(accountId: string) {
  return request<ScanJob>(`/cloud-accounts/${accountId}/scan`, { method: "POST" });
}

export function getScanStatus(accountId: string) {
  return request<ScanJob>(`/cloud-accounts/${accountId}/scan-status`);
}

export function analyzeAccount(accountId: string) {
  return request<AnalysisResult>(`/cloud-accounts/${accountId}/analyze`, { method: "POST" });
}

export function getReport(accountId: string) {
  return request<OptimizationReportOut>(`/cloud-accounts/${accountId}/report`);
}

export { ApiError };
