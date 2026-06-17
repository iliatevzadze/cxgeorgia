/**
 * API base URL for browser requests.
 *
 * Default (empty string): same-origin `/api/v1/...` via Next.js rewrites.
 * Override with NEXT_PUBLIC_API_URL when calling the backend directly.
 */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return "";
}

export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base = getApiBaseUrl();
  return base ? `${base}${normalizedPath}` : normalizedPath;
}
