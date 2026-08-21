import { API_URL } from "./constants";

/**
 * Builds a WebSocket URL from the same API_URL used for REST calls.
 * API_URL is often relative (e.g. "/api/v1") so the current page origin
 * is used as the base, and http(s) is swapped for ws(s).
 */
export function buildWsUrl(path: string): string {
  const base = API_URL.startsWith("http")
    ? API_URL
    : `${window.location.origin}${API_URL}`;
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}${path}`;
}
