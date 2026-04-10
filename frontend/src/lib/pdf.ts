import { setTokenGetter } from './api';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function isDemoMode(): boolean {
  return sessionStorage.getItem('kerf_demo') === 'true';
}

/**
 * Token getter reference — set by the auth provider via api.ts setTokenGetter.
 * Re-used here to get auth tokens for PDF download requests.
 */
let _tokenGetter: (() => Promise<string | null>) | null = null;

/**
 * Register the token getter for PDF downloads.
 * Called automatically when setTokenGetter is called in api.ts.
 */
export function setPdfTokenGetter(getter: () => Promise<string | null>): void {
  _tokenGetter = getter;
}

async function getAuthToken(): Promise<string | null> {
  if (isDemoMode()) return 'demo-token';
  if (_tokenGetter) return _tokenGetter();
  return null;
}

/**
 * Download a PDF from the backend API.
 *
 * In demo mode this falls back to window.print() since there is no real
 * backend to generate the PDF.
 *
 * @param endpoint - API path relative to BASE_URL, e.g. "/me/documents/doc_123/pdf"
 * @param filename - Suggested download filename, e.g. "Safety-Plan.pdf"
 */
export async function downloadPdf(
  endpoint: string,
  filename: string,
): Promise<void> {
  if (isDemoMode()) {
    window.print();
    return;
  }

  const token = await getAuthToken();

  const headers: Record<string, string> = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error(`PDF generation failed (${response.status})`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
