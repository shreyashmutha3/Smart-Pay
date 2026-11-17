import { ReconciliationResponse, ValidateResponse, SampleDataResponse } from '../types';

/**
 * Resolves the backend API base URL:
 * - Checks VITE_API_BASE_URL (standard) and VITE_API_URL (backward-compatible)
 * - In local dev (import.meta.env.DEV), safely falls back to 'http://localhost:8000'
 * - In production builds without an explicit environment variable, defaults to '' (relative root proxying)
 */
const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim() !== '') {
    return envUrl.trim().replace(/\/+$/, '');
  }
  return import.meta.env.DEV ? 'http://localhost:8000' : '';
};

const API_BASE = getApiBaseUrl();

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSampleData(): Promise<SampleDataResponse> {
  const res = await fetch(`${API_BASE}/api/v1/sample-data`);
  if (!res.ok) throw new Error(`Failed to load sample data: ${res.statusText}`);
  return res.json();
}

export async function validateData(
  platformFile: File | null,
  bankFile: File | null,
  useSampleData: boolean
): Promise<ValidateResponse> {
  const formData = new FormData();
  formData.append('use_sample_data', String(useSampleData));
  if (!useSampleData) {
    if (platformFile) formData.append('platform_file', platformFile);
    if (bankFile) formData.append('bank_file', bankFile);
  }

  const res = await fetch(`${API_BASE}/api/v1/validate`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Validation request failed');
  }
  return res.json();
}

export async function runReconciliation(
  platformFile: File | null,
  bankFile: File | null,
  reportingPeriod: string,
  roundingTolerance: string,
  useSampleData: boolean
): Promise<ReconciliationResponse> {
  const formData = new FormData();
  formData.append('reporting_period', reportingPeriod);
  formData.append('rounding_tolerance', roundingTolerance);
  formData.append('use_sample_data', String(useSampleData));

  if (!useSampleData) {
    if (platformFile) formData.append('platform_file', platformFile);
    if (bankFile) formData.append('bank_file', bankFile);
  }

  const res = await fetch(`${API_BASE}/api/v1/reconcile`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || 'Reconciliation failed');
  }
  return res.json();
}

export function getFullExportUrl(runId: string): string {
  return `${API_BASE}/api/v1/reconciliations/${runId}/export`;
}

export function getExceptionsExportUrl(runId: string): string {
  return `${API_BASE}/api/v1/reconciliations/${runId}/exceptions`;
}
